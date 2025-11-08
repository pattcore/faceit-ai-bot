const tf = require('@tensorflow/tfjs-node');
const fs = require('fs');

// Загрузка данных из файла
function loadTrainingData() {
  const rawData = fs.readFileSync('user_data.json', 'utf-8').split('\n').filter(Boolean);
  const parsedData = rawData.map((line) => JSON.parse(line));

  const inputs = parsedData.map((entry) => [entry.userId, entry.action.length]);
  const outputs = parsedData.map((entry) => [entry.result]);

  return { inputs, outputs };
}

const { inputs, outputs } = loadTrainingData();
const trainingData = tf.tensor2d(inputs);
const outputData = tf.tensor2d(outputs);

// Создание модели
async function trainModel() {
  const model = tf.sequential();

  model.add(tf.layers.dense({
    inputShape: [2],
    units: 4,
    activation: 'relu',
  }));

  model.add(tf.layers.dense({
    units: 1,
    activation: 'sigmoid',
  }));

  model.compile({
    optimizer: 'adam',
    loss: 'meanSquaredError',
  });

  

  await model.fit(trainingData, outputData, {
    epochs: 100,
    callbacks: {
      onEpochEnd: (epoch, logs) => {
        console.log(`Эпоха ${epoch + 1}: Потери = ${logs.loss}`);
      },
    },
  });

  

  // Сохранение модели
  await model.save('file://./model');
}

trainModel().catch(console.error);