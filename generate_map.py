import cta_tracker

def generate_map_html():
    """Generates the map.html file."""
    m = cta_tracker.create_map()
    m.save("map.html")

if __name__ == "__main__":
    generate_map_html()
