import ast


def parse_raw_triplets(raw_triplets: str):
    raw_triplets.replace('"', '')
    try:
        structured_triplets = ast.literal_eval(raw_triplets)
    except Exception as e:
        print(raw_triplets)
        print(str(e))
        print('ERROR!')
    
    print('----------')
    print('RAW:')
    print(raw_triplets)
    print('----------')
    return structured_triplets

def parse_relation_definition(raw_definitions: str):
    descriptions = raw_definitions.split('\n')
    relation_definitions_dict = {}

    for description in descriptions:
        if ':' not in description:
            continue
        index_of_colon = description.index(':')
        relation = description[:index_of_colon].strip()

        relation_description = description[index_of_colon + 1 :].strip()

        relation_definitions_dict[relation] = relation_description
    
    print('----------')
    print('RAW:')
    print(raw_definitions)
    print('----------')
    return relation_definitions_dict