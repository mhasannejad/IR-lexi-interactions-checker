import pandas as pd
import re

from main import search_lexi_db_for_generic, \
    get_lexi_category_from_lexi_id_generic, get_all_interactions_two_by_two, get_IR_generic_names, \
    pure_ingreds_from_IR_generic_names, in_paranthesis_extract

input_IR_generic_codes = list(pd.read_csv('droped.csv')['generic_ir'])
IR_generic_names = get_IR_generic_names(input_IR_generic_codes)

salts = []
other_names = []
numbers = []
for ingred in IR_generic_names:
    in_paranthesis_txt = in_paranthesis_extract(ingred)
    if not in_paranthesis_txt:
        continue

    if mo:=re.search(r'AS (.*)', in_paranthesis_txt):
        salts.append([ingred, mo.group(1)])
    elif mo:=re.search(r'(\d)|(\d-\d)', in_paranthesis_txt):
        # for example adult cold preparation 4-2
        numbers.append((ingred, in_paranthesis_txt))
    else:
        other_names.append((ingred, in_paranthesis_txt))

pd.DataFrame(salts).to_csv('lists created by me\\salts.csv')
pd.DataFrame(numbers).to_csv('lists created by me\\preparation_numbers.csv')
pd.DataFrame(other_names).to_csv('lists created by me\\other_names.csv')



