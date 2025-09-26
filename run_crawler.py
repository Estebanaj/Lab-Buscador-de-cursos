from crawler import go

if __name__ == "__main__":
    # puedes ajustar el número de páginas
    go(n=50, dictionary="courses.json", output="index.csv")
    print("✅ Listo: se generaron index.csv y courses.json")