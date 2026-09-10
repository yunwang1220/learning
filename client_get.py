import PropertyApiClient

client = PropertyApiClient(
    "https://api.company.com"
)

properties = client.get_properties()

property_record = client.get_property(1001)