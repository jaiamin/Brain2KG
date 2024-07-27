import ast


def parse_raw_triplets(raw_triplets: str):
    raw_triplets.replace('"', '')
    try:
        structured_triplets = ast.literal_eval(raw_triplets)
    except Exception as e:
        print('------')
        print(raw_triplets)
        print(str(e))
        print('ERROR!')
    
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
        except IndexError:
            print('------')
            print(raw_definitions)
            print('ERROR!')
    
    return relation_definitions_dict