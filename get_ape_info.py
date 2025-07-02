from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
import json

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# Load contract ABI
with open('ape_abi.json', 'r') as f:
    abi = json.load(f)

############################
# Connect to an Ethereum node using your Infura endpoint
api_url = "https://mainnet.infura.io/v3/5e1abd5de2ac4dbda6e952eddc4394ca"
provider = HTTPProvider(api_url)
web3 = Web3(provider)

def get_ape_info(ape_id):
    assert isinstance(ape_id, int), f"{ape_id} is not an int"
    assert 0 <= ape_id, f"{ape_id} must be at least 0"
    assert 9999 >= ape_id, f"{ape_id} must be less than 10,000"

    data = {'owner': "", 'image': "", 'eyes': ""}

    # 1. Connect to the BAYC contract
    contract = web3.eth.contract(address=contract_address, abi=abi)
    
    # 2. Get owner address
    owner_address = contract.functions.ownerOf(ape_id).call()
    data['owner'] = owner_address
    
    # 3. Get token URI from the contract
    token_uri = contract.functions.tokenURI(ape_id).call()
    
    # 4. Fetch metadata from IPFS
    ipfs_hash = token_uri.replace("ipfs://", "")
    
    # Try different IPFS gateways (ordered by reliability)
    gateways = [
        "https://ipfs.io/ipfs/",
        "https://gateway.pinata.cloud/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/",
        "https://ipfs.infura.io:5001/api/v0/cat?arg="
    ]
    
    metadata = None
    for gateway in gateways:
        try:
            if "infura" in gateway:
                # Infura requires POST request
                response = requests.post(gateway + ipfs_hash)
            else:
                response = requests.get(gateway + ipfs_hash, timeout=10)
            
            if response.status_code == 200:
                metadata = response.json()
                break
        except Exception as e:
            print(f"Failed with gateway {gateway}: {str(e)}")
            continue
    
    if not metadata:
        raise Exception("Could not fetch metadata from IPFS after trying multiple gateways")
    
    # 5. Extract image and eyes attributes
    data['image'] = metadata.get('image', '')
    
    # Find eyes attribute in traits
    attributes = metadata.get('attributes', [])
    for attr in attributes:
        if attr.get('trait_type', '').lower() == 'eyes':
            data['eyes'] = attr.get('value', '')
            break

    assert isinstance(data, dict), f'get_ape_info{ape_id} should return a dict'
    assert all([a in data.keys() for a in 
                ['owner', 'image', 'eyes']]), f"return value should include the keys 'owner','image' and 'eyes'"
    return data
