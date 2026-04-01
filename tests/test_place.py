"""Tests for Place model classes."""

import pytest

from models.place import Place


class TestPlace:
    def test_create_with_required_fields(self):
        p = Place(id="driftmoor", name="Driftmoor Town")
        assert p.id == "driftmoor"
        assert p.name == "Driftmoor Town"

    def test_defaults(self):
        p = Place(id="t", name="T")
        assert p.description == ""
        assert p.parent_id is None
        assert p.children == []
        assert p.connections == []
        assert p.who_is_here == []
        assert p.place_raw == ""
        assert p.contents_raw == ""
        assert p.dynamic_state == {}

    def test_list_defaults_are_independent(self):
        p1 = Place(id="a", name="A")
        p2 = Place(id="b", name="B")
        p1.children.append("x")
        p1.connections.append("y")
        assert p2.children == []
        assert p2.connections == []

    def test_dict_defaults_are_independent(self):
        p1 = Place(id="a", name="A")
        p2 = Place(id="b", name="B")
        p1.dynamic_state["threat"] = "high"
        assert p2.dynamic_state == {}

    def test_with_all_fields(self):
        p = Place(
            id="mayors_hall",
            name="The Mayor's Hall",
            parent_id="driftmoor",
            description="The largest building.",
            children=["mayors_office", "records_room", "living_quarters"],
            connections=["Village square"],
            who_is_here=["Aldren Thorne", "Elise Harper"],
        )
        assert p.parent_id == "driftmoor"
        assert len(p.children) == 3
        assert "Aldren Thorne" in p.who_is_here

    def test_is_root(self):
        root = Place(id="region", name="Region")
        child = Place(id="town", name="Town", parent_id="region")
        assert root.parent_id is None
        assert child.parent_id == "region"
