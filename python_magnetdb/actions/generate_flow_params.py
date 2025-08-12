import os
import shutil
from python_magnetdb.models import Magnet

def generate_flow_params(magnet: Magnet, directory: str, flow_prefix: str=None):
    """
    Generate flow parameters for a given magnet and directory.
    
    :param magnet: The magnet object containing the necessary data.
    :param directory: The directory where the flow will be executed.
    :param flow_prefix: The prefix of the flow to be generated.
    """

    flow_name = "flow_params"
    if flow_prefix is not None:
        flow_name = f"{flow_prefix}_{flow_name}"

    if magnet.flow_params:
        print(f"get magnet.flow_params: flow_params={magnet.flow_params}, type={type(magnet.flow_params)}")
        print(f"save to: {os.getcwd()}/{flow_name}.json")
    else:
        print(f"generate_site_directory: {os.getcwd()}/{flow_name}.json")
        shutil.copyfile(f"{os.getcwd()}/flow_params.json", f"{directory}/{flow_name}.json")

    pass