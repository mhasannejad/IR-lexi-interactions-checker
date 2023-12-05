import pandas as pd
from pandas import DataFrame

from main import search_lexi_db_for_generic, \
    get_lexi_category_from_lexi_id_generic, get_all_interactions_two_by_two, get_IR_generic_names, \
    pure_ingreds_from_IR_generic_names, in_paranthesis_detect, main_search_for_each_IR_generic_in_lexi, \
    select_right_adminstration_route_from_lexi

# input_IR_generic_codes = [1911, 5992, 584]  # Atorvastatin, Gemfibrozil, Fenofibrate
# input_IR_generic_codes = [1911, 5992,584, 52173, 1016]
# input_IR_generic_codes = [2336, 5629, 17886, 2091, 53, 63]  # pantoprazol, losartan, meropenem, vancomycin, ondansetron, amikasin, amiodaron
input_IR_generic_codes = [11504, 5629]  # pantoprazol, losartan, meropenem, vancomycin, ondansetron, amikasin, amiodaron


IR_generic_dict = get_IR_generic_names(input_IR_generic_codes)

drug_category_ids = {}  # this dict maps generic id to category id

for IR_generic_id, drug_details in IR_generic_dict.items():

    is_combination, ingredients, _, IR_generic_name, brand, route_of_admin = drug_details.values()
    print('\n================')
    print(f'\n{IR_generic_id=}')
    print(f'{route_of_admin=}')

    for ingredient in ingredients:

        generic_id, rows = main_search_for_each_IR_generic_in_lexi(ingredient)
        if rows:
            if len(rows) >1:
                generic_id = select_right_adminstration_route_from_lexi(route_of_admin, rows)

        # category_ids = get_lexi_category_from_lexi_id_generic(generic_id)
        # drug_category_ids[generic_id] = category_ids
        category_ids = get_lexi_category_from_lexi_id_generic(generic_id)
        drug_category_ids[generic_id] = {'category_ids': category_ids,
                                         'IR_generic_id': IR_generic_id}

print(drug_category_ids)
result = get_all_interactions_two_by_two(drug_category_ids)
# print(result)
# DataFrame(result).to_csv('lists created by me\\result.csv')
