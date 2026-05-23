from behaviordrafts.activegraph_adapter import ActiveGraphAdapter


class _AGObject:
    def __init__(self, id_, type_, data):
        self.id = id_
        self.type = type_
        self.data = data


class _AGRelation:
    def __init__(self, id_, source, target, type_, data):
        self.id = id_
        self.source = source
        self.target = target
        self.type = type_
        self.data = data


class _MethodGraph:
    def __init__(self):
        self._objects = [_AGObject("o1", "Summary", {"first_sentence": "A.", "line_count": 1})]
        self._relations = [_AGRelation("r1", "o1", "f1", "summarizes", {"weight": 1})]

    def all_objects(self):
        return list(self._objects)

    def all_relations(self):
        return list(self._relations)

    def objects(self, type=None):
        return [o for o in self._objects if type is None or o.type == type]

    def relations(self, source=None, target=None, type=None):
        out = self._relations
        if source is not None:
            out = [r for r in out if r.source == source]
        if target is not None:
            out = [r for r in out if r.target == target]
        if type is not None:
            out = [r for r in out if r.type == type]
        return out


def test_normalize_object_from_activegraph_shape():
    rt = ActiveGraphAdapter(allow_local_shim=True)
    obj = _AGObject("obj-1", "Summary", {"first_sentence": "Hello.", "line_count": 2})
    assert rt.normalize_object(obj) == {"id": "obj-1", "type": "Summary", "first_sentence": "Hello.", "line_count": 2}


def test_normalize_relation_from_activegraph_shape():
    rt = ActiveGraphAdapter(allow_local_shim=True)
    rel = _AGRelation("rel-1", "summary-1", "file-1", "summarizes", {"confidence": 0.7})
    assert rt.normalize_relation(rel) == {
        "id": "rel-1",
        "type": "summarizes",
        "from": "summary-1",
        "to": "file-1",
        "confidence": 0.7,
    }


def test_object_and_relation_count_use_method_graph_not_len_on_method():
    rt = ActiveGraphAdapter(allow_local_shim=True)
    rt._ag_graph = _MethodGraph()
    assert rt.object_count() == 1
    assert rt.relation_count() == 1
    assert rt.all_objects()[0]["type"] == "Summary"
    assert rt.all_relations()[0]["type"] == "summarizes"
