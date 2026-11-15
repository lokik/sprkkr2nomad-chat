""" Functions in this module are used to create NOMAD schema
form ASE2SPRKKR schema of input parameters """

import numpy as np

from nomad.metainfo import Quantity, MEnum, SubSection
from nomad.datamodel import ArchiveSection

from ase2sprkkr.common.grammar_types import (
    TypedGrammarType,
    Keyword,
    BasicSeparator,
    Array,
    Range
)
from ase2sprkkr.common.alternative_types import numpy_types
from ase2sprkkr.common.value_definitions import ValueDefinition
from .class_utils import camelize, create_class


def nomad_class_name(definition):
    """ Returns the name that should be used for NOMAD class corresponding
    to a given definition """
    return camelize(definition.name) + 'SprkkrInputParametersSection'


def value_to_nomad(definition):
    """ Convert a ASE2SPRKKR value definition to a NOMAD one. """
    gt = definition.type
    description = definition.description(True)
    if definition.is_repeated.is_numbered:
        section = create_class(
                        nomad_class_name(definition),
                        (ArchiveSection,),
                        { 'index': Quantity(type=int),
                          'is_default': Quantity(type=bool, description='Wildcard value for unspecified numbered indices.'),
                          'value': grammar_type_to_nomad(gt) },
                        description
                  )
        out = SubSection(sub_section=section, repeats=True)
    else:
        out = grammar_type_to_nomad(gt, description)
    return out


def grammar_type_to_nomad(gt, description=None, shape=None):
    """ Create a NOMAD value definition that is able to hold a given type.
    Returns None, if there is no sense to pass such value to NOMAD,
    e.g. if it is separator, or a fixed value
    """
    if isinstance(gt, TypedGrammarType):
        typ = gt.numpy_type
        if typ is object:
            typ = str
        if shape:
            typ = numpy_types[typ]
    elif isinstance(gt, Keyword):
        if len(gt.keywords) <= 1:
            return None
        typ = MEnum(*gt.keywords)
    elif isinstance(gt, BasicSeparator):
        return None
    elif isinstance(gt, Array):
        if gt.min_length == gt.max_length and gt.min_length is not None:
            shape = [ gt.min_length ]
        else:
            mlen = gt.max_length if gt.max_length is not None else "*"
            shape = [ f'{gt.min_length or 0}..{mlen}' ]
        return grammar_type_to_nomad(gt.type, description, shape)
    elif isinstance(gt, Range):
        return grammar_type_to_nomad(gt._type, description, [2])
    else:
        raise ValueError("This ASE2SPRKKR is not supported to be converted to NOMAD")
    return Quantity(type=typ, description=description, shape=shape)


def definition_to_nomad(definition):
    """
    Convert a ASE2SPRKKR value/section definition to NOMAD one.
    """
    if definition.is_hidden:
        return None
    if isinstance(definition, ValueDefinition):
        return value_to_nomad(definition)
    return section_to_nomad(definition)


def section_to_nomad(definition):
    """
    Convert ASE2SPRKKR section definition to NOMAD one.
    """

    def members():
        for i in definition:
            v = definition_to_nomad(i)
            if v:
                yield i.name.lower(), v

    childs = {i:v for i,v in members()}
    section = create_class(
                           nomad_class_name(definition),
                           (ArchiveSection,), childs,
                           definition.description()
              )
    return SubSection(sub_section = section)


def nomad_section_from_sprkkr(nomad_class, data):
    """ Create a NOMAD Section of a given class from given
    ASE2SPRKKR configuration section (e.g. input_parameters).
    The class could be created e.g. by :func:`section_to_nomad`.
    """

    # Use all values (explicit + defaults) so input_parameters are complete.
    dct = data.to_dict() or {}

    def normalize(value, section_cls=None):
        # NumPy arrays/scalars from ASE2SPRKKR are not directly suitable for
        # NOMAD's MEnum quantities or for its ordinary JSON-like metainfo.
        if isinstance(value, np.ndarray):
            return normalize(value.tolist(), section_cls)
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, (list, tuple)):
            return [normalize(item, section_cls) for item in value]
        if not isinstance(value, dict):
            return value

        # A sparse, numbered ASE2SPRKKR value is a dictionary such as
        # {"def": 1.0, 2: 2.0}. NOMAD expects a list of repeated sections.
        # Apply this translation only to sections with the generated
        # index/value schema; ordinary dictionaries are not numbered values.
        subsections = (
            section_cls.m_def.all_sub_sections if section_cls is not None else {}
        )
        result = {}
        for key, item in value.items():
            name = key.lower() if isinstance(key, str) else key
            sub = subsections.get(name)
            if sub is None:
                result[name] = normalize(item)
                continue

            child_cls = sub.sub_section.section_cls
            if sub.repeats and {'index', 'is_default', 'value'} <= set(
                child_cls.m_def.all_quantities
            ):
                if isinstance(item, dict):
                    items = []
                    for index, entry in item.items():
                        if index == 'def':
                            items.append({
                                'is_default': True,
                                'value': normalize(entry),
                            })
                        else:
                            # ASE2SPRKKR normally supplies int keys, but
                            # serialized input can also contain digit strings.
                            index = int(index)
                            if index < 1:
                                raise ValueError('Numbered SPR-KKR indices must be positive')
                            items.append({
                                'index': index,
                                'value': normalize(entry),
                            })
                else:
                    items = item
                result[name] = normalize(items, child_cls)
            else:
                result[name] = normalize(item, child_cls)
        return result

    out = nomad_class.m_from_dict(normalize(dct, nomad_class))
    return out
