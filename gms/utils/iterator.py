def get_event_loop():
    import asyncio
    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:  # pragma: lax no cover
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop


def stream_async_iterator(async_iter):
    """Bridge for AsyncIterator to Synchronous Generator."""
    
    loop = get_event_loop()
    while True:
        try:
            # Drive the async iterator inside a one-off loop run
            yield loop.run_until_complete(anext(async_iter))
        except StopAsyncIteration:
            break
            