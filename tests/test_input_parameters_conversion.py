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
    value = Quantity(type=int)


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
    assert [(item.index, item.value) for item in converted.numbered] == [
        (1, 11), (2, 12),
    ]
