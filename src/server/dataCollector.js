const fs = require('fs');

// Пример сбора данных пользователей
function collectUserData(userId, action, result) {
  const data = {
    userId,
    action,
    result,
    timestamp: new Date().toISOString(),
  };

  // Сохранение данных в файл
  fs.appendFileSync('user_data.json', JSON.stringify(data) + '\n');
  
}

module.exports = { collectUserData };