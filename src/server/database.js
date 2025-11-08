const { Sequelize } = require('sequelize');

// Initialize Sequelize with SQLite for simplicity
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: './database.sqlite',
});

// Define User model
const User = sequelize.define('User', {
  username: {
    type: Sequelize.STRING,
    allowNull: false,
  },
  email: {
    type: Sequelize.STRING,
    allowNull: false,
    unique: true,
  },
  password: {
    type: Sequelize.STRING,
    allowNull: false,
  },
});

// Define Subscription model
const Subscription = sequelize.define('Subscription', {
  level: {
    type: Sequelize.STRING,
    allowNull: false,
  },
  price: {
    type: Sequelize.FLOAT,
    allowNull: false,
  },
});

// Relationships
User.hasOne(Subscription);
Subscription.belongsTo(User);

// Sync database
sequelize.sync({ force: true }).then(() => {
  
});

module.exports = { sequelize, User, Subscription };