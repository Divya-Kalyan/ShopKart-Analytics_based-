from app import create_app

app = create_app()  # analytics_bp already registered inside

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  ShopKart eCommerce App")
    print("  URL: http://127.0.0.1:5000")
    print("  Admin: admin@shopkart.com / admin123")
    print("="*50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)