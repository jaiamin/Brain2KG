import ast

from brain2kg import get_logger

logger = get_logger(__name__)


def parse_raw_triplets(raw_triplets: str):
    raw_triplets.replace('"', '')
    while raw_triplets and not raw_triplets.startswith('['):
        raw_triplets = raw_triplets[1:]
    while raw_triplets and not raw_triplets.endswith(']'):
        raw_triplets = raw_triplets[:-1]
    try:
        structured_triplets = ast.literal_eval(raw_triplets)
    except Exception as e:
        logger.error(str(e))
        return None
        
    return structured_triplets

def parse_relation_definition(raw_definitions: str, relations: list[str]):
    descriptions = raw_definitions.split('\n')
    relation_definitions_dict = {}

    for idx, description in enumerate(descriptions):
        if ':' not in description:
            continue
        index_of_colon = description.index(':')
        relation_description = description[index_of_colon + 1 :].strip()

        try:
            relation_definitions_dict[relations[idx]] = relation_description
        except Exception as e:
            logger.error(str(e))
            return None
    
    return relation_definitions_dict