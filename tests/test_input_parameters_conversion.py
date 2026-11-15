"""Regression tests for NumPy-backed SPR-KKR values in NOMAD metainfo."""

from types import SimpleNamespace

import numpy as np
import pytest
from nomad.datamodel import ArchiveSection
from nomad.metainfo import MEnum, Quantity, SubSection

from sprkkr2nomad.parsers.ase2sprkkr_to_nomad import nomad_section_from_sprkkr


class ArraySettings(ArchiveSection):
    grid = Quantity(type=MEnum('3', '5'), shape=['*'])
    single = Quantity(type=MEnum('3', '5'))
    iterations = Quantity(type=int)
    vectors = Quantity(type=np.float64, shape=[2])


class NumberedValue(ArchiveSection):
    index = Quantity(type=int)
    is_default = Quantity(type=bool)
    value = Quantity(type=float)


class ConvertedParameters(ArchiveSection):
    settings = SubSection(sub_section=ArraySettings)
    numbered = SubSection(sub_section=NumberedValue, repeats=True)


@pytest.mark.parametrize('enum_array', [
    np.array(['3'], dtype=object),
    np.array(['5', '3'], dtype=object),
])
def test_nomad_accepts_numpy_enum_arrays_and_scalars(enum_array):
    data = SimpleNamespace(to_dict=lambda: {
        'SETTINGS': {
            'GRID': enum_array,
            'SINGLE': np.array('3', dtype=object),
            'ITERATIONS': np.int64(7),
            'VECTORS': np.array([1.25, 2.5]),
        },
        'NUMBERED': {1: np.int64(11), 2: np.int64(12)},
    })

    converted = nomad_section_from_sprkkr(ConvertedParameters, data)

    assert list(converted.settings.grid) == enum_array.tolist()
    assert converted.settings.single == '3'
    assert converted.settings.iterations == 7
    np.testing.assert_allclose(converted.settings.vectors, [1.25, 2.5])
    assert [(item.index, bool(item.is_default), item.value) for item in converted.numbered] == [
        (1, False, 11.0), (2, False, 12.0),
    ]


@pytest.mark.parametrize('numbered, expected', [
    ({'def': np.float64(1.0)}, [(None, True, 1.0)]),
    ({'def': np.float64(1.0), 2: np.float64(2.5)}, [
        (None, True, 1.0), (2, None, 2.5),
    ]),
    ({'1': np.float64(3.0), 4: np.float64(5.0)}, [
        (1, None, 3.0), (4, None, 5.0),
    ]),
])
def test_numbered_values_preserve_default_and_indices(numbered, expected):
    data = SimpleNamespace(to_dict=lambda: {'NUMBERED': numbered})
    converted = nomad_section_from_sprkkr(ConvertedParameters, data)
    assert [(item.index, bool(item.is_default), item.value) for item in converted.numbered] == [
        (index, bool(is_default), value) for index, is_default, value in expected
    ]
