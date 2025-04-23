from pandas import read_excel

# Read in raw .xlsx data
referendums_src = "./data/referendums/Mistni_referenda-tabulka_hlaseni_-_20250121.xlsx"
df = read_excel(referendums_src, header = 0, skiprows = 1, skipfooter = 11)

# Name columns
column_names = ['nr', 'obec_okres_kraj_', 'otazka', 'datum', 'opravnene_osoby', 'ucast_perc', 'platnost_', 'vysledek', 'hm1', 'zavaznost', 'hm2']
df.columns = column_names
print(df)
