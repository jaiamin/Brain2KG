import re
import ast

from brain2kg import get_logger

logger = get_logger(__name__)


def parse_raw_triplets(raw_triplets: str):
    # handle regular incorrect LLM outputs
    raw_triplets = raw_triplets.replace(' ', '') # remove spaces
    raw_triplets = raw_triplets.replace('"', "'") # replace double with single quotes
    inner_string_pattern = r"(?<!\[)(?<!',)\'(?!,')(?!\])"
    raw_triplets = re.sub(inner_string_pattern, '', raw_triplets) # remove inner string quotes
    while raw_triplets and not raw_triplets.startswith('['):
        raw_triplets = raw_triplets[1:]
    while raw_triplets and not raw_triplets.endswith(']'):
        raw_triplets = raw_triplets[:-1]
    if not raw_triplets.startswith('[['):
        raw_triplets = '[[' + raw_triplets[1:]
    if not raw_triplets.endswith(']]'):
        raw_triplets = raw_triplets[:-1] + ']]'

    logger.debug(f'PARSED TRIPLET (REGULAR): {raw_triplets}')
    try:
        structured_triplets = ast.literal_eval(raw_triplets)
    except Exception as e:
        logger.error(str(e))
        raw_triplets = _fallback_triplet_parser(raw_triplets)
        logger.debug(f'PARSED TRIPLET (FALLBACK): {raw_triplets}')
        structured_triplets = ast.literal_eval(raw_triplets)
    
    for triplet in structured_triplets:
        try:
            assert len(triplet) == 3
        except AssertionError:
            logger.error('Triplet does not contain exactly 3 elements.')
            raw_triplets = _fallback_triplet_parser(raw_triplets)
            logger.debug(f'INCORRECT TRIPLET (2ND FALLBACK): {triplet}')
            structured_triplets = ast.literal_eval(raw_triplets)
            break

    return structured_triplets

def _fallback_triplet_parser(incorrect_raw_triplets: str):
    brackets_pattern = r'\]+(\s|,)*\[+'
    raw_triplets = re.sub(brackets_pattern, '],[', incorrect_raw_triplets, flags=re.DOTALL)
    return raw_triplets

def parse_relation_definition(raw_definitions: str, relations: set[str]) -> dict:
    raw_definitions = _clean_definition_text(raw_definitions)
    descriptions = raw_definitions.split('\n')
    relation_definitions_dict = {}

    for description in descriptions:
        if not description.strip():
            continue
        if ':' not in description:
            logger.error(f'Raw definitions cannot be parsed.')
            return None
        index_of_colon = description.index(':')
        relation = description[:index_of_colon].strip()
        
        # ensure relation is provided in camelcase naming convention (one-word)
        # relation_split = relation.split()
        # if len(relation_split) > 1:
        #     logger.warn(f'WARNING (incorrect relation naming convention): {raw_definitions}')
        #     relation_split = list(map(str.title, relation_split))
        #     relation_split[0] = relation_split[0].lower()
        #     relation = ' '.join(relation_split)
        # else:
        #     relation = relation[:1].lower() + relation[1:]

        # handle incorrect LLM output for relation camelcase naming convention
        relation = relation.replace(' ', '')
        found = False
        for rel in relations:
            if rel.lower() == relation.lower():
                found = True
                relation = rel
                break
        if not found:
            logger.error(f'Relation {relation} is not a valid relation.')
            logger.debug(f'PARSED RELATION: {relation}')
            logger.debug(f'AVAILABLE RELATIONS: {relations}')
            return None

        relation_description = description[index_of_colon + 1 :].strip()

        try:
            relation_definitions_dict[relation] = relation_description
        except Exception as e:
            logger.error(str(e))
            return None
    
    return relation_definitions_dict

def _clean_definition_text(text: str):
    return ''.join(char for char in text if char.isalpha() or char in ': .\n')