from baku_fc.runtime import create_app

app = create_app(3)

if __name__ == "__main__":
    app.run()
