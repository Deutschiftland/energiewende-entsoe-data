#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import glob
import os

#def concat_year_from_month(year, country, type):
year = 2016
country = 'FR'
type = 'production'

df = pd.concat([pd.read_csv(f) for f in glob.glob(f'./data/{year}*{country}*{type}.csv')])
df = df.sort_values('date')
df.to_csv(f"./data/{year}0101-{year}1231_{country}_{type}.csv")