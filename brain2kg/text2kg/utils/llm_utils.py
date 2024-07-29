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
    
    for triplet in structured_triplets:
        assert len(triplet) == 3
    return structured_triplets

def parse_relation_definition(raw_definitions: str, relations: set[str]) -> dict:
    descriptions = raw_definitions.split('\n')
    relation_definitions_dict = {}

    for description in descriptions:
        if ':' not in description:
            continue
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
        for rel in relations:
            if rel.lower() == relation.lower():
                relation == rel
                break
        assert relation in relations

        relation_description = description[index_of_colon + 1 :].strip()

        try:
            relation_definitions_dict[relation] = relation_description
        except Exception as e:
            logger.error(str(e))
            return None
    
    return relation_definitions_dict