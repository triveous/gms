from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import frappe
from docling_core.types.doc.document import DoclingDocument, ImageRef

PROMPT_PICTURE_DESCRIPTION_SIMPLE = "Describe this document picture in a few sentences."
CHUNK_SUMMARIZATION_TEMPLATE = """<document>
{{WHOLE_DOCUMENT}}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{{CHUNK_CONTENT}}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""


class DoclingImageUploader(ABC):
    """
    Base class for uploading assets to a remote storage.
    This will mutate the existing document with ImageRef objects pointing to the uploaded assets.
    """

    def run(self, doc: DoclingDocument):
        for idx, pic in enumerate(doc.pictures):
            if not pic.image:
                continue
            if not self.get_doc_id(doc=doc):
                raise ValueError("Document id is not set.")

            image_name = "_".join(
                [
                    self.get_doc_id(doc=doc),
                    f"{doc.origin.binary_hash:016X}",
                    str(idx + 1),
                    f".{pic.image.pil_image.format.lower() if pic.image.pil_image.format else 'png'}",
                ]
            )

            updated_image = self.save(pic.image, image_name)
            pic.image = updated_image

    @staticmethod
    def get_doc_id(doc: DoclingDocument):
        return doc.name

    @abstractmethod
    def get_prefix(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def save(self, pil: ImageRef, file_name: str) -> ImageRef:
        raise NotImplementedError


class DoclingImageUploaderFrappe(DoclingImageUploader):
    root_dir: str
    folder_created = False

    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = root_dir

    def get_prefix(self):
        if not self.folder_created:
            file = frappe.new_doc("File")
            file.is_folder = 1
            if "/" in self.root_dir:
                file.file_name = self.root_dir.split("/")[-1]
                file.folder = "/".join(self.root_dir.split("/")[:-1])
            else:
                file.file_name = self.root_dir
                file.folder = "Home"
            file.insert(ignore_if_duplicate=True)
            self.folder_created = True
        return self.root_dir

    def save(self, image_ref: ImageRef, file_name: str) -> ImageRef:
        pil_image = image_ref.pil_image
        buff = BytesIO()
        pil_image.save(
            buff,
            format=image_ref.mimetype.split("/")[1].upper(),
        )
        file = frappe.get_doc(
            {
                "doctype": "File",
                "folder": self.get_prefix(),
                "file_name": file_name,
                "is_private": 1,
                "content": buff.getvalue(),
            }
        ).save(ignore_permissions=True)

        frappe.log(f"File url {file.file_url}")

        return ImageRef(
            mimetype=image_ref.mimetype,
            uri=Path(file.file_url),
            size=image_ref.size,
            dpi=image_ref.dpi,
            _pil=pil_image,
        )
