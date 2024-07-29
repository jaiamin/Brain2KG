import os
import csv
import copy
import pathlib

import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

from tqdm import tqdm
from brain2kg import get_logger

from brain2kg.text2kg.utils.text_utils import preprocess_text
from brain2kg.text2kg.extractor import TripletExtractor
from brain2kg.text2kg.definer import SchemaDefiner
from brain2kg.text2kg.aligner import SchemaAligner

logger = get_logger(__name__)


class EDA:
    def __init__(self, **eda_configuration) -> None:

        # OIE module setting
        self.oie_llm_name = eda_configuration['oie_llm']
        self.oie_prompt_template_file_path = eda_configuration['oie_prompt_template_file_path']
        self.oie_few_shot_example_file_path = eda_configuration['oie_few_shot_example_file_path']

        # Schema Definition module setting
        self.sd_llm_name = eda_configuration['sd_llm']
        self.sd_template_file_path = eda_configuration['sd_prompt_template_file_path']
        self.sd_few_shot_example_file_path = eda_configuration['sd_few_shot_example_file_path']

        # Schema Alignment module setting
        self.sa_target_schema_file_path = eda_configuration['sa_target_schema_file_path']
        self.sa_verifier_llm_name = eda_configuration['sa_llm']
        self.sa_embedding_model_name = eda_configuration['sa_embedding_model']
        self.sa_template_file_path = eda_configuration['sa_prompt_template_file_path']

        self.target_schema_dict = {}

        reader = csv.reader(open(self.sa_target_schema_file_path, 'r'))
        for row in reader:
            relation, relation_definition = row
            self.target_schema_dict[relation] = relation_definition

        # EDA initialization
        extractor = TripletExtractor(model=self.oie_llm_name)
        logger.info('Extractor initialized.')
        definer = SchemaDefiner(model=self.sd_llm_name)
        logger.info('Definer initialized.')
        aligner = SchemaAligner(
            target_schema_dict=self.target_schema_dict,
            embedding_model_str=self.sa_embedding_model_name,
            verifier_model_str=self.sa_verifier_llm_name
        )
        logger.info('Aligner initialized.')

        self.extractor = extractor
        self.definer = definer
        self.aligner = aligner

    def extract_kg(
        self,
        input_raw_text: str,
        output_dir: str = None,
    ):
        if output_dir is not None:
            pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

        output_kg_list = []

        # preprocess text
        input_raw_text = preprocess_text(input_raw_text)

        # sentence tokenize input text
        sentences = sent_tokenize(input_raw_text)
        logger.info('Input text sentence tokenized.')

        # EDA run
        oie_triplets, schema_definition_dict_list, aligned_triplets_list = self._extract_kg_helper(sentences)
        output_kg_list.append(oie_triplets)
        output_kg_list.append(aligned_triplets_list)

        if output_dir is not None:
            with open(os.path.join(output_dir, 'eda_output.txt'), 'w') as f:
                for l in aligned_triplets_list:
                    f.write(str(l) + '\n')
                f.flush()

        return output_kg_list

    def _extract_kg_helper(
        self,
        input_text_list: list[str],
    ):
        oie_triplets_list = []
        
        oie_prompt_template_str = open(self.oie_prompt_template_file_path).read()
        oie_few_shot_examples_str = open(self.oie_few_shot_example_file_path).read()
        for idx in tqdm(range(len(input_text_list)), desc='Extracting'):
            input_text = input_text_list[idx]
            oie_triplets = self.extractor.extract(
                input_text,
                oie_prompt_template_str,
                oie_few_shot_examples_str,
            )
            oie_triplets_list.append(oie_triplets)
        logger.info('All sentences extracted.')

        schema_definition_dict_list = []
        schema_definition_few_shot_prompt_template_str = open(self.sd_template_file_path).read()
        schema_definition_few_shot_examples_str = open(self.sd_few_shot_example_file_path).read()

        schema_definition_relevant_relations_dict = {}

        # define the relations in the induced open schema
        for idx, oie_triplets in enumerate(tqdm(oie_triplets_list, desc='Defining')):
            schema_definition_dict = self.definer.define_schema(
                input_text_list[idx],
                oie_triplets,
                schema_definition_few_shot_prompt_template_str,
                schema_definition_few_shot_examples_str,
            )
            schema_definition_dict_list.append(schema_definition_dict)

            for relation, relation_definition in schema_definition_dict.items():
                schema_definition_relevant_relations = self.aligner.retrieve_relevant_relations(
                    relation_definition,
                    top_k=5,
                )
                schema_definition_relevant_relations_dict[relation] = schema_definition_relevant_relations
        logger.info('All sentences defined and relations found.')

        schema_aligner_prompt_template_str = open(self.sa_template_file_path).read()

        # Target Alignment
        aligned_triplets_list = []
        for idx, oie_triplets in enumerate(tqdm(oie_triplets_list, desc='Aligning')):
            aligned_triplets = []
            for oie_triplet in oie_triplets:
                relation = oie_triplet[1]

                # if relation is exact match with any relevant relation, no need to llm_verify
                if relation in schema_definition_relevant_relations_dict[relation][0].keys():
                    aligned_triplet = [oie_triplet[0], relation, oie_triplet[2]]
                else:
                    aligned_triplet = self.aligner.llm_verify(
                        input_text_list[idx],
                        oie_triplet,
                        schema_definition_dict_list[idx][relation],
                        schema_aligner_prompt_template_str,
                        schema_definition_relevant_relations_dict[relation][0]
                    )
                if aligned_triplet is not None:
                    aligned_triplets.append(aligned_triplet)
            aligned_triplets_list.append(aligned_triplets)
        logger.info('All sentences aligned.')

        return oie_triplets_list, schema_definition_dict_list, aligned_triplets_list