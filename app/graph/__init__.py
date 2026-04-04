def build_graph(*args, **kwargs):
    from .builder import build_graph as _build_graph

    return _build_graph(*args, **kwargs)


__all__ = ["build_graph"]
