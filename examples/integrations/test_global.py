from mycelium import portal

@portal.share(name="MyCloudAgent", description="Test agent via tunnel")
def hello(query: str):
    return f"Hello from Mycelium Tunnel! You sent: {query}"

if __name__ == "__main__":
    hello.serve()