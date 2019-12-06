import os
import pandas as pd
from utils import get_abs_path
from get_gauge_network_comids import format_intermediate


def get_all_feather_files():
    """
    get a list of the feather files from a folder that has a bunch of feather
    files that contain the "cat" nhd attributes ("cat" meaning that the
    attributes are for the individual catchment and not accumulated)
    :return: list of feather files
    """
    feather_dir = "D:/nhd/feather"
    feather_files = []
    for path, subdirs, files in os.walk(feather_dir):
        for f in files:
            if f.endswith('cat.feather'):
                f_path = os.path.join(path, f)
                feather_files.append(f_path)
    return feather_files


def read_nhd_categories():
    """
    read the nhd categories to include
    """
    nhd_category_file = get_abs_path('../data/tables/nhd_categories_filtered.csv')
    df = pd.read_csv(nhd_category_file)
    nhd_cats = df['ID'].to_list()
    return nhd_cats


def get_blank_df(feather_file):
    """
    generate a blank dataframe with the nhd comids as the index. the desired
    nhd attribute values can then be added to this as new columns
    :param feather_file: [str] path to any feather file that has the nhd comids
    as a column named 'COMID'
    :return: [pandas df] blank pandas df with index set
    """
    df = pd.read_feather(feather_file)
    df_blank = pd.DataFrame(index=df['COMID'])
    return df_blank


def get_categories_in_feather(nhd_cats, columns):
    """
    get a filtered set of columns in a dataframe. the filter is a list of nhd 
    catchment attributes that we are interested in. if none of the columns are
    in the attributes that we are interested in, it will return an empty index
    :param nhd_cats: [list] list of nhd attributes that we are interested in
    :param columns: [pandas index] a pandas index of the columns that we are 
    potentially interested in
    :return: [pandas index] a pandas index with the columns that are in the nhd
    catchment attributes that we are interested in
    """
    in_cats = columns[columns.isin(nhd_cats)]
    return in_cats


def filter_combine_nhd_files(out_file):
    """
    combine attributes from a bunch of feather files that contain all of the 
    nhd catchment attributes into one file. only select attributes are combined
    however, and these attributes are specified in a
    "nhd_categories_filtered.csv" file and read in via the
    'read_nhd_categories' method. The filtered and combined dataframe is 
    written to a parquet file
    :param out_file:[str] path to where the output file should be written
    :returns: [pandas df] combined and filtered pandas dataframe
    """
    feather_files = get_all_feather_files()
    nhd_cats = read_nhd_categories()
    df_combined = get_blank_df(feather_files[0])
    for feather_file in feather_files:
        df = pd.read_feather(feather_file)
        df.set_index('COMID', inplace=True)
        cols = get_categories_in_feather(nhd_cats, df.columns)
        if len(cols) > 0:
            df_combined[cols] = df[cols]
    df_combined = df_combined.reset_index()
    df_combined.to_parquet(out_file)
    return df_combined


def combine_attr_to_nwis_net(nwis_inter_net, filt_comb_nhd, out_file):
    """
    consolidate the intermediate catchment attributes for the nwis network
    :param nwis_inter_net:[str] path to the nwis intermediate network csv file.
    this file should have two columns:'comid' and 'intermediate_comid'
    :param filt_comb_nhd:[str] path to the filtered, combined nhd catchment
    attributes parquet file
    :param out_file:[str] path to where the consolidated data should be written
    :returns: none
    """
    inter_df = pd.read_csv(nwis_inter_net)
    inter_df = format_intermediate(inter_df)

    nhd_df = pd.read_parquet(filt_comb_nhd)
    nhd_df.set_index('COMID', inplace=True)
    inter_df = inter_df.join(nhd_df)
    inter_df = inter_df.groupby('dissolve_comid').mean()
    inter_df.to_parquet(out_file)

