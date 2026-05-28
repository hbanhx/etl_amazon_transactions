import logging
import os
# from extract import extract
# from transform import transform
# import openpyxl

def load_data(load_dfs):
    logging.info("Starting data load")

    base = os.path.dirname(os.path.abspath(__file__))

    for dir, dfs in load_dfs.items():
        dir_path = os.path.join(base, f"{dir}")
        os.makedirs(dir_path, exist_ok=True)

        for name, df in dfs.items():
            path = os.path.join(dir_path, f"{name}.xlsx")
            df.to_excel(path, index=False)
            logging.info(f"Saved {name} file: {os.path.relpath(path)}")

    logging.info("Data load complete")