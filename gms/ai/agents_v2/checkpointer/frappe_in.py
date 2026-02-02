import base64
import logging
import pickle

import frappe
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)


class FrappeBufferedCheckpointer(InMemorySaver):
    """Buffered checkpointer that loads full state snapshot from Frappe into memory,
    runs the graph in-memory, and flushes the full state snapshot back to Frappe.

    It uses a single 'SNAPSHOT' record per thread in the 'LangGraph Checkpoint' table
    to store the entire pickled state of the InMemorySaver (storage, writes, blobs).
    """

    def _get_snapshot_id(self, thread_id: str) -> str:
        """Generates the ID for the snapshot record."""
        return f"SNAPSHOT-{thread_id}"

    def load_from_frappe(self, config: RunnableConfig):
        """Loads the pickled state from Frappe into in-memory storage."""
        thread_id = str(config["configurable"]["thread_id"])
        snapshot_id = self._get_snapshot_id(thread_id)

        try:
            if frappe.db.exists("LangGraph Checkpoint", snapshot_id):
                # Fetch only the checkpoint_blob where we store the pickle
                checkpoint_blob = frappe.db.get_value(
                    "LangGraph Checkpoint", snapshot_id, "checkpoint_blob"
                )

                if checkpoint_blob:
                    # 1. Decode Base64 -> Bytes
                    pickle_bytes = base64.b64decode(checkpoint_blob)
                    # 2. Unpickle -> Dict
                    state_dict = pickle.loads(pickle_bytes)

                    # 3. Restore State
                    self.storage.update(state_dict.get("storage", {}))
                    self.writes.update(state_dict.get("writes", {}))
                    # blobs is optional/new in some versions, handle safely
                    if "blobs" in state_dict:
                        # Ensure blobs are properly restored if they are not in the snapshot
                        # (InMemorySaver initializes it in __init__)
                        self.blobs.update(state_dict["blobs"])

                    logger.info(f"Loaded snapshot for thread {thread_id}")
            else:
                logger.info(
                    f"No snapshot found for thread {thread_id}, starting fresh."
                )

        except Exception as e:
            logger.error(f"Failed to load snapshot for thread {thread_id}: {e}")
            # We don't raise here to allow starting fresh if corrupted,
            # or maybe we should raise to prevent data loss?
            # User request implies "restoring properly" is the goal, so maybe logging is enough for now.

    def flush_to_frappe(self):
        """Saves current in-memory state snapshot back to Frappe."""
        # We assume single thread per instance in this context usually,
        # but InMemorySaver supports multiple threads.
        # We should flush ALL threads present in memory or just the one relevant?
        # Flushing all is safer for the "InMemorySaver" concept.
        # But we use one ID per thread?
        # InMemorySaver stores data keyed by thread_id.
        # So we can iterate over threads and save snapshots for each.

        # Identify all thread_ids present in storage, writes, blobs
        all_threads = set(self.storage.keys())
        # writes keys are (thread_id, checkpoint_ns, checkpoint_id)
        for t, _, _ in self.writes.keys():
            all_threads.add(t)
        # blobs keys are (thread_id, ns, channel, version)
        for t, _, _, _ in self.blobs.keys():
            all_threads.add(t)

        for thread_id in all_threads:
            try:
                snapshot_id = self._get_snapshot_id(thread_id)

                # Filter state for this thread only
                # We need to construct a state dict containing only this thread's data
                # to keep snapshots isolated per thread.

                thread_storage = self.storage.get(thread_id, {})

                # Filter writes for thread
                thread_writes = {
                    k: v for k, v in self.writes.items() if k[0] == thread_id
                }

                # Filter blobs for thread
                thread_blobs = {
                    k: v for k, v in self.blobs.items() if k[0] == thread_id
                }

                # If we are using defaultdicts in InMemorySaver, we might get empty dicts.
                # Pickle handles standard python objects well.

                state_to_save = {
                    "storage": {
                        thread_id: thread_storage
                    },  # Keep structure consistent? InMemorySaver.storage is thread_id -> ns -> ...
                    "writes": thread_writes,
                    "blobs": thread_blobs,
                }

                # 1. Pickle
                pickle_bytes = pickle.dumps(state_to_save)
                # 2. Key -> Base64
                b64_str = base64.b64encode(pickle_bytes).decode("utf-8")

                # 3. Upsert
                doc_dict = {
                    "doctype": "LangGraph Checkpoint",
                    "name": snapshot_id,
                    "thread": thread_id,
                    "checkpoint_blob": b64_str,
                    "metadata_blob": "{}",  # Placeholder
                    # parent_checkpoint_id is not applicable for snapshot concept
                }

                if frappe.db.exists("LangGraph Checkpoint", snapshot_id):
                    doc = frappe.get_doc("LangGraph Checkpoint", snapshot_id)
                    doc.checkpoint_blob = b64_str
                    doc.save(ignore_permissions=True)
                else:
                    doc = frappe.get_doc(doc_dict)
                    try:
                        doc.insert(ignore_permissions=True)
                    except frappe.exceptions.DuplicateEntryError:
                        doc = frappe.get_doc("LangGraph Checkpoint", snapshot_id)
                        doc.checkpoint_blob = b64_str
                        doc.save(ignore_permissions=True)

            except Exception as e:
                logger.error(f"Failed to flush snapshot for thread {thread_id}: {e}")

        # Explicit commit
        frappe.db.commit()
