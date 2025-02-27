# PrimeOrganics Backend

This is the backend service for **PrimeOrganics**, an API-powered system for managing organic product transactions, inventory, and orders.

## 🚀 Features
- User authentication & authorization (JWT-based)
- Product management (CRUD operations)
- Order processing & tracking
- Inventory management
- Secure API endpoints

## 🛠️ Tech Stack
- **Node.js** with **Express.js** (Backend framework)
- **MongoDB** (Database)
- **Mongoose** (ODM for MongoDB)
- **JWT** (Authentication)
- **Cloudinary** (For media uploads, if applicable)

## 📌 Getting Started

### 1️⃣ Clone the repository
```bash
$ git clone https://github.com/kimaninyutu/primeorganicsbackend.git
$ cd primeorganicsbackend
```

### 2️⃣ Install dependencies
```bash
$ npm install
```

### 3️⃣ Set up environment variables
Create a `.env` file in the root directory and configure the following:
```
PORT=5000
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_secret_key
CLOUDINARY_URL=your_cloudinary_url  # If using Cloudinary
```

### 4️⃣ Run the development server
```bash
$ npm start
```

## 📡 API Endpoints
### Authentication
| Method | Endpoint         | Description |
|--------|----------------|-------------|
| POST   | `/api/auth/register` | Register a new user |
| POST   | `/api/auth/login`    | Login & get token |

### Products
| Method | Endpoint         | Description |
|--------|----------------|-------------|
| GET    | `/api/products` | Get all products |
| POST   | `/api/products` | Create a new product |
| PUT    | `/api/products/:id` | Update a product |
| DELETE | `/api/products/:id` | Delete a product |

### Orders
| Method | Endpoint         | Description |
|--------|----------------|-------------|
| GET    | `/api/orders` | Get all orders |
| POST   | `/api/orders` | Place a new order |
| PUT    | `/api/orders/:id` | Update order status |
| DELETE | `/api/orders/:id` | Cancel an order |

## 🧪 Running Tests
```bash
$ npm test
```

## 📜 License
This project is licensed under the [MIT License](LICENSE).

---
### ✨ Contributions
Feel free to fork the repo, create a feature branch, and submit a pull request!

💡 Have a question? Open an issue or contact me at [nyutukimani01@gmail.com](mailto:nyutukimani01@gmail.com).

