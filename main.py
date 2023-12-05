import difflib
import re
from typing import Any

import pandas as pd
from sqliteframe import Database, table, String, Integer, Boolean
from pathlib import Path
from itertools import combinations


def read_sqlite_database(database_path: str):
    database = Database(Path(database_path), output=False)
    return database


def extract_columns(file_path: str):
    df = pd.read_excel(file_path, usecols="I,N")
    df = df.rename(columns={"I": "generic_ir", "N": "ingredient"})
    return df


db = read_sqlite_database('interact.db')

with db.connection(commit=True) as data:
    # Execute any statements while a connection is open
    rows = data.execute("select name from category").fetchall()
    forms = []
    for i in rows:
        mo = re.search(r'.*\((.*)\)', i[0])
        if mo:
            t = mo.group(1)
            forms.append(t)
    print(len(set(forms)))


def make_unique_IR_generic_excel():
    df = pd.read_excel('data.xlsx')
    df = df[['ingredient', 'generic_ir', 'generic_name', 'brand']]
    df.drop_duplicates(subset=['generic_ir'], inplace=True)
    df.to_excel('lists created by me\\unique_IR_generic_data.xlsx')


generic_iran_data = pd.read_excel('lists created by me\\unique_IR_generic_data.xlsx')
salts = pd.read_csv('lists created by me\\salts.csv')


def dosage_form_extract(IR_generic_name, ingredient):
    dosage_form_and_dose = IR_generic_name.replace(ingredient + ' ', '')
    dosage_form_and_route = re.split(' \d+', dosage_form_and_dose)[0]
    route = dosage_form_and_route.strip().split(' ')[-1]
    route = re.sub(r'\(|\)', '', route)
    route = route.lower()
    return route


def get_ingredients_for_generic_code(generic_id):
    # this file have unique not duplicated generics
    _, ingredient, IR_generic_id, IR_generic_name, brand = \
        generic_iran_data[generic_iran_data['generic_ir'] == generic_id].iloc[0]
    return ingredient, IR_generic_id, IR_generic_name, brand


def get_IR_generic_names(IR_generic_codes: list[int]):
    IR_generic_names = []
    IR_generic_dict = {}

    for generic_id in IR_generic_codes:
        ingredient, IR_generic_id, IR_generic_name, brand = get_ingredients_for_generic_code(generic_id)
        route_of_adminstration = dosage_form_extract(IR_generic_name, ingredient)
        if ' / ' in ingredient:
            IR_generic_dict[generic_id] = {'is_combination': True,
                                           'ingredients': ingredient.split(' / '),
                                           'IR_generic_id': IR_generic_id,
                                           'IR_generic_name': IR_generic_name,
                                           'brand': brand,
                                           'dossage_form': route_of_adminstration}
        else:
            IR_generic_dict[generic_id] = {'is_combination': False,
                                           'ingredients': [ingredient],
                                           'IR_generic_id': IR_generic_id,
                                           'IR_generic_name': IR_generic_name,
                                           'brand': brand,
                                           'dossage_form': route_of_adminstration}

    return IR_generic_dict


def pure_ingreds_from_IR_generic_names(drugs: list[str]):
    pure_ingreds = []
    salts = []
    pure_export = []
    for drug in drugs:
        if '/' in drug:
            ingreds = drug.split('/')
            pure_ingreds.extend([(ingred).strip() for ingred in ingreds])
        else:
            pure_ingreds.append(drug.strip())

    for ingred in pure_ingreds:
        drug, salt = in_paranthesis_extract(ingred)
        if salt:
            salts.append((ingred, salt))
        pure_export.append(drug)

    print(pure_export)

    return pure_export, salts


def in_paranthesis_extract(ingred: str):
    mo = re.search(r'(.*) ?\((.*)\)', ingred)
    if mo:
        drug, in_paranthesis_txt = mo.groups()
        return drug.strip(), in_paranthesis_txt.strip()
    else:
        return None, None


def in_paranthesis_detect(ingred):
    drug_without_paranthesis, in_paranthesis_txt = in_paranthesis_extract(ingred)
    if not in_paranthesis_txt:
        return {'type': 'no_paranthesis',
                'response': ingred}
    elif mo := re.search(r'AS (.*)', in_paranthesis_txt):
        return {'type': 'salt',
                'salt': mo.group(1),
                'ingred': drug_without_paranthesis}
    elif ' AS ' in in_paranthesis_txt:
        # for examples Betamethasone (betameethasone AS ...)
        return {'type': 'salt',
                'salt': in_paranthesis_txt.split(' AS ')[-1],
                'ingred': drug_without_paranthesis}

    elif mo := re.search(r'(\d+)|(\d+-\d+)', in_paranthesis_txt):
        # for example adult cold preparation 4-2
        return {'type': 'preparation_number',
                'number': in_paranthesis_txt,
                'ingred': drug_without_paranthesis}

    elif in_paranthesis_txt in ['HUMAN', 'HUMAN PLASMA DERIVED', 'CONCENTRATED', 'RECOMBINANT']:
        return {'type': 'protein_type',
                'ingred': drug_without_paranthesis,
                'source': in_paranthesis_txt,
                'full_name': ingred}
    else:
        return {'type': 'other_name',
                'other_name': in_paranthesis_txt,
                'ingred': drug_without_paranthesis}


def search_lexi_db_for_generic(ingredient: str) -> (int | None, list[int]):
    with db.connection(commit=True) as data:
        # Execute any statements while a connection is open
        prompt = f"select id, name from generic where lower(name)='{ingredient.lower()}' "
        rows = data.execute(prompt).fetchall()

        print('\n', prompt)
        print(f'{ingredient=} {rows=}')
        if rows:
            return rows[0][0], rows
        else:
            prompt = f"select id, name from generic where lower(name) like '{ingredient.lower()}%' "
            rows = data.execute(prompt).fetchall()
            print('\n', prompt)
            print(f'{ingredient=} {rows=}')

            if rows:
                return rows[0][0], rows
            print(f'\n>>> {ingredient} not found in lexi generics')
            return None, None


def search_lexi_db_for_brand(ingredient: str) -> int | None:
    with db.connection(commit=True) as data:
        # for exam;e
        prompt = f"select generic_id, name from brand where lower(name) like '%{ingredient.lower()} %' "
        rows = data.execute(prompt).fetchall()
        print('\n', prompt)
        if rows:
            print(f'in Brands searchd: {rows=}')
            return rows[0][0], rows

        print(f'>>> {ingredient} not found in lexi brands')
        return None, None


def search_if_no_paranthesis(IR_generic):
    generic_id, rows = search_lexi_db_for_generic(IR_generic)
    if not generic_id:
        generic_id, rows = search_lexi_db_for_brand(IR_generic)
        if not generic_id:
            # maybe salt without paranthesis for example: metformin hydrochloride
            splitted = IR_generic.split(' ')[:-1]
            if splitted:
                generic_id, rows = search_lexi_db_for_generic(' '.join(splitted))
                if not generic_id:
                    #  exmaple: ASA => asprin maybe we can find it in lexi brand names
                    generic_id, rows = search_lexi_db_for_brand(' '.join(splitted))
                    # if not generic_id:
                    #     generic_id, rows = search_by_similarity(' '.join(splitted))

    return generic_id, rows


def select_right_adminstration_route_from_lexi(route_of_admin, rows):
    generic_id = None

    if route_of_admin in ['topical', 'ophthalmic', 'otic', 'nasal']:
        for row in rows:
            if f'({route_of_admin})' in row[1].lower():
                generic_id = row[0]

    elif route_of_admin == 'respiratory':
        for row in rows:
            if '(oral inhalation)' in row[1].lower():
                generic_id = row[0]

        if not generic_id:
            for row in rows:
                if '(systemic)' in row[1].lower():
                    generic_id = row[0]


    elif route_of_admin == 'vaginal':
        for row in rows:
            if '(topical)' in row[1].lower():
                generic_id = row[0]

    else:
        for row in rows:
            if '(systemic)' in row[1].lower() or '(conventional)' in row[1].lower():
                generic_id = row[0]

    if not generic_id:
        without_and = [row for row in rows if ' and ' not in row[1].lower()]
        row = min(without_and, key=lambda i: len(i[1]))  # this mf returns short item string
        generic_id = row[0]

    return generic_id


def search_by_similarity(IR_generic):
    with db.connection(commit=True) as data:
        prompt = f"select name from generic "
        rows = data.execute(prompt).fetchall()
        drugs_names = [i[0] for i in rows]
        substrings = [IR_generic[i:i + 5] for i in range(0, len(IR_generic), 5)]
        best_matches = {}

        # Iterate over each substring
        matches_found = []
        for substring in substrings:
            # Find the best match in the list_of_strings
            matches = difflib.get_close_matches(substring, drugs_names, n=1)

            # If a match is found, add it to the dictionary
            if len(matches) > 0:
                matches_found.append(matches[0])
                best_matches[substring] = matches[0]
        if len(matches_found) > 0:
            matches_found = [f"'{i}'" for i in matches_found]
            prompt = f'select * from generic where name in ({",".join(matches_found)})'
            print(prompt)
            drugs_matched = data.execute(prompt).fetchall()
            return drugs_matched[0][0], drugs_matched
        else:
            return None, None


def main_search_for_each_IR_generic_in_lexi(IR_generic):
    generic_id, rows = None, None
    response = in_paranthesis_detect(IR_generic)
    print(f'{response=}')
    if response['type'] == 'no_paranthesis':
        generic_id, rows = search_if_no_paranthesis(IR_generic)

    elif response['type'] == 'salt':
        pure_ingred = response['ingred']
        generic_id, rows = search_lexi_db_for_generic(pure_ingred)
        if not generic_id:
            generic_id, rows = search_lexi_db_for_brand(pure_ingred)
    elif response['type'] == 'preparation_number':
        # TODO assume most complex manner for examaple adult cold with 4 compounds
        pass
    elif response['type'] == 'protein_type':
        # for exmaple: (Recombinant) or (human)
        ingred = response['ingred']
        source = response['source']
        full_name = response['full_name']
        generic_id, rows = search_lexi_db_for_generic(ingred)

    elif response['type'] == 'other_name':
        # first search by first name if not found search by other name or search first in lexi brand names
        ingred, other_name = response['ingred'], response['other_name']
        generic_id, rows = search_lexi_db_for_brand(ingred)
        if not generic_id:
            generic_id, rows = search_lexi_db_for_brand(other_name)

        # if not generic_id:
        #     generic_id, rows = search_by_similarity(ingred)

    if not generic_id:
        generic_id, rows = search_lexi_db_for_brand(IR_generic)

    return generic_id, rows


def get_lexi_category_from_lexi_id_generic(lexi_generic_id) -> list[(int,)]:
    if lexi_generic_id is None:
        return []
    with db.connection(commit=True) as data:
        # Execute any statements while a connection is open
        category_ids = data.execute(
            f"select category_id from category_generic_xref where generic_id={lexi_generic_id} ").fetchall()
        print(f"select category_id from category_generic_xref where generic_id={lexi_generic_id}")
        category_ids = [id[0] for id in category_ids]
        print(category_ids)
        return category_ids


def get_all_interactions(drug_category_ids):
    print('\n*** ALL catgs method:')
    with db.connection(commit=True) as data:
        # Execute any statements while a connection is open
        list_of_categories = ','.join(drug_category_ids)
        monographs = data.execute(
            f"select * from monograph where object_id in ({list_of_categories} and precipitant_id in ({list_of_categories}))").fetchall()
        print(
            f"select * from monograph where object_id in ({list_of_categories} and precipitant_id in ({list_of_categories}))")
        risks = [i[1] for i in monographs]
        print(risks)
        return monographs


def interaction_id_to_class(risk):
    risk_dict = {1: 'A',
                 2: 'B',
                 3: 'C',
                 4: 'D',
                 5: 'X'}

    return risk_dict[risk]


def get_generic_name_for_lexi_generic_code(generic_code):
    with db.connection(commit=True) as data:
        generic_name = data.execute(f'select name from generic where id={generic_code}').fetchall()
        print(generic_code)
        return generic_name[0][0]


def get_all_interactions_two_by_two(drug_category_ids):
    print('\n*** Permutation method:')
    result = []
    with db.connection(commit=True) as data:

        # Execute any statements while a connection is open
        all_combs = combinations(drug_category_ids, r=2)
        monographs = []
        for drug1, drug2 in all_combs:

            catgs1 = ','.join([str(i) for i in drug_category_ids[drug1]['category_ids']])
            catgs2 = ','.join([str(i) for i in drug_category_ids[drug2]['category_ids']])

            query = f"select * from monograph where (object_id in ({catgs1}) and precipitant_id in ({catgs2})) or (precipitant_id in ({catgs1}) and object_id in ({catgs2}))"
            print('\n', get_generic_name_for_lexi_generic_code(drug1), 'AND',
                  get_generic_name_for_lexi_generic_code(drug2))
            drug_1_name = get_generic_name_for_lexi_generic_code(drug1)
            drug_2_name = get_generic_name_for_lexi_generic_code(drug2)

            drug_1_IR_generic = drug_category_ids[drug1]['IR_generic_id']
            drug_2_IR_generic = drug_category_ids[drug2]['IR_generic_id']

            monographs = data.execute(query).fetchall()

            print(query)
            risks = [i[1] for i in monographs]
            summaries = [(i[4], i[8]) for i in monographs]

            if risks:
                idx = risks.index(max(risks))
                risk = risks[idx]
                summary, management = summaries[idx]
                print(max(risks))
                print(interaction_id_to_class(max(risks)))
            else:
                print('-No interactions founds-')
                risk = ' No interaction found'
                summary, management = None, None

            result.append({
                'drug_1_IR_generic': drug_1_IR_generic,
                'drug_2_IR_generic': drug_2_IR_generic,
                'drug_1_name': drug_1_name,
                'drug_2_name': drug_2_name,
                'risk': risk,
                'summary': summary,
                'management': management
            })

    return result
