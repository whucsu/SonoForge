"""Tests for constructor ReferenceModel."""

from __future__ import annotations

import pytest

from echo_personal_tool.constructor.models import (
    NormRangeModel,
    ParameterModel,
    PathologyModel,
    ReferenceModel,
    TopicModel,
)


@pytest.fixture
def sample_model() -> ReferenceModel:
    return ReferenceModel(
        topics=[
            TopicModel(
                name="Левый желудочек",
                slug="left_ventricle",
                pathologies=[
                    PathologyModel(
                        name="Диастолическая функция",
                        slug="lv_diastolic",
                        parameters=[
                            ParameterModel(
                                id="ea_ratio",
                                name="Соотношение E/A",
                                unit="",
                                norm_male=NormRangeModel(low=0.8, high=2.0),
                                norm_female=NormRangeModel(low=0.8, high=2.0),
                            )
                        ],
                    )
                ],
            )
        ]
    )


class TestReferenceModel:
    def test_round_trip(self, sample_model: ReferenceModel) -> None:
        data = sample_model.to_dict()
        restored = ReferenceModel.from_dict(data)
        assert len(restored.topics) == 1
        assert restored.topics[0].slug == "left_ventricle"

    def test_deep_copy(self, sample_model: ReferenceModel) -> None:
        copy = sample_model.deep_copy()
        copy.topics[0].name = "Modified"
        assert sample_model.topics[0].name == "Левый желудочек"

    def test_get_topic(self, sample_model: ReferenceModel) -> None:
        topic = sample_model.get_topic("left_ventricle")
        assert topic is not None
        assert topic.name == "Левый желудочек"

        assert sample_model.get_topic("nonexistent") is None

    def test_get_pathology(self, sample_model: ReferenceModel) -> None:
        patho = sample_model.get_pathology("left_ventricle", "lv_diastolic")
        assert patho is not None
        assert patho.name == "Диастолическая функция"

        assert sample_model.get_pathology("left_ventricle", "nonexistent") is None
        assert sample_model.get_pathology("nonexistent", "lv_diastolic") is None

    def test_find_parameter(self, sample_model: ReferenceModel) -> None:
        result = sample_model.find_parameter("ea_ratio")
        assert result is not None
        topic, patho, param = result
        assert topic.slug == "left_ventricle"
        assert patho.slug == "lv_diastolic"
        assert param.name == "Соотношение E/A"

        assert sample_model.find_parameter("nonexistent") is None

    def test_all_param_ids(self, sample_model: ReferenceModel) -> None:
        ids = sample_model.all_param_ids()
        assert "ea_ratio" in ids

    def test_all_image_paths(self) -> None:
        model = ReferenceModel(
            topics=[
                TopicModel(
                    name="T",
                    slug="t",
                    pathologies=[
                        PathologyModel(
                            name="P",
                            slug="p",
                            image_paths=["img1.png", "img2.jpg"],
                        )
                    ],
                )
            ]
        )
        paths = model.all_image_paths()
        assert paths == {"img1.png", "img2.jpg"}


class TestPathologyModel:
    def test_has_gradations(self) -> None:
        patho = PathologyModel(
            name="P",
            slug="p",
            gradations=[
                {"name": "Mild", "parameters": []},
            ],
        )
        assert patho.has_gradations

        patho_flat = PathologyModel(name="P2", slug="p2", parameters=[])
        assert not patho_flat.has_gradations

    def test_all_parameters_flat(self) -> None:
        param = ParameterModel(id="p1", name="P1", unit="")
        patho = PathologyModel(name="P", slug="p", parameters=[param])
        assert patho.all_parameters() == [param]

    def test_all_parameters_gradations(self) -> None:
        param1 = ParameterModel(id="p1", name="P1", unit="")
        param2 = ParameterModel(id="p2", name="P2", unit="")
        patho = PathologyModel(
            name="P",
            slug="p",
            gradations=[
                {"name": "Mild", "parameters": [param1.to_dict()]},
                {"name": "Severe", "parameters": [param2.to_dict()]},
            ],
        )
        all_params = patho.all_parameters()
        assert len(all_params) == 2
        assert all_params[0].id == "p1"
        assert all_params[1].id == "p2"
