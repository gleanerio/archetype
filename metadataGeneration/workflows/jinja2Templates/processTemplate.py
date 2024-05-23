import json
import re
import pandas as pd
from jinja2 import Template
from pyld import jsonld


def proc_FIP(row):
    kwd = {"ID": row['ID'], "url": row['Url'],
        "doi": row['DOI'], "name": row['Title'],
        "description": row['Description'], "license": row['License'], "type": row['Type'] }
    
    for key in kwd:
        if isinstance(kwd[key], str):
            # remove control characters and returns with spaces
            kwd[key] = re.sub(r'[\r\n\t"]+', ' ', kwd[key])

    # read template and alter
    with open("smallTemplate.json", "r") as file:
        template_str = file.read()

    template = Template(template_str)
    populated_json = template.render(kwd)

    print(populated_json)

    nt = ""
    try:
        json_data = json.loads(populated_json)
        try:
            nt = jsonld.normalize(json_data, {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)

    print(nt)

    return nt


def main():
    df = pd.read_csv('../GDSC_metadata.csv', dtype=str)  # read all as strings for now
    
    # remove any rows where there is NAN in the desired columns
    column_names = ['ID', 'Url', 'DOI', 'Title', 'Description', 'License', 'Type']
    df = df.dropna(subset=column_names, how='any')
    
    # apply a function to build the RDF in a new Column 
    df['rdf'] = df.apply(proc_FIP, axis=1)
    
    # print(df['rdf'].head())
    print(len(df))

    df['rdf'].to_string('GDSC_metadata_out.nt', index=False)


if __name__ == '__main__':
    main()
