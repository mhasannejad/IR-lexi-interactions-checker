import pandas as pd

from main import search_lexi_db_for_generic, main_search_for_each_IR_generic_in_lexi, \
    get_lexi_category_from_lexi_id_generic, get_all_interactions_two_by_two, get_IR_generic_names, \
    pure_ingreds_from_IR_generic_names, get_generic_name_for_lexi_generic_code, \
    select_right_adminstration_route_from_lexi

input_IR_generic_codes = list(pd.read_excel('lists created by me\\unique_IR_generic_data.xlsx')['generic_ir'])

IR_generic_dict = get_IR_generic_names(input_IR_generic_codes)

drug_category_ids = {}  # this dict maps generic id to category id
export_found_not_found = []
for IR_generic_id, drug_details in IR_generic_dict.items():

    is_combination, ingredients, _, IR_generic_name, brand, route_of_admin = drug_details.values()
    print('\n================')
    print(f'\n{IR_generic_id=}')
    print(f'{route_of_admin=}')

    for ingredient in ingredients:

        generic_id, rows = main_search_for_each_IR_generic_in_lexi(ingredient)
        if rows is not None:
            if len(rows) > 1:
                generic_id = select_right_adminstration_route_from_lexi(route_of_admin, rows)
        else:
            rows = [['', '', '']]
        lexi_generic_name = get_generic_name_for_lexi_generic_code(generic_id) if generic_id else None
        print(f'{IR_generic_id=}, {IR_generic_name=}, {generic_id=}, {lexi_generic_name=}')

        t_dict = {
            'IR_generic_id': IR_generic_id,
            'IR_generic_name': IR_generic_name,
            'Ingredient': ingredient,
            'lexi_generic_id': str(generic_id),
            'lexi_generic_name': lexi_generic_name,
            'rows_in_db': ' | '.join([row[1] for row in rows]),
            'catgs': ''
        }

        category_ids = get_lexi_category_from_lexi_id_generic(generic_id)
        drug_category_ids[generic_id] = category_ids
        t_dict['catgs'] = '|'.join([str(i) for i in category_ids])
        export_found_not_found.append(t_dict)

df = pd.DataFrame(export_found_not_found)
df.sort_values(by='lexi_generic_id', ascending=False).to_csv('lists created by me\\export_not_found (sorted)new.csv')
df.to_csv('lists created by me\\export_not_found.csv')

# salts_df = pd.DataFrame(salts)
# salts_df.to_csv('salts.csv')
# get_all_interactions_two_by_two(drug_category_ids)
