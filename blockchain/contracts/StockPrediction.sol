// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract StockPrediction {

    struct Prediction {

        string stockName;

        // Prices are stored ×100.
        // Example: ₹4055.73 → 405573
        uint256 currentPrice;
        uint256 predictedPrice;

        string direction;

        uint256 confidence;
        uint256 upProbability;
        uint256 downProbability;

        int256 signalScore;

        uint256 stopLoss;
        uint256 targetPrice;

        uint256 timestamp;
    }

    Prediction[] public predictions;

    event PredictionAdded(
        uint256 indexed predictionId,
        string stockName,
        string direction,
        uint256 currentPrice,
        uint256 predictedPrice,
        uint256 confidence,
        uint256 timestamp
    );

    function addPrediction(
        string memory _stockName,
        uint256 _currentPrice,
        uint256 _predictedPrice,
        string memory _direction,
        uint256 _confidence,
        uint256 _upProbability,
        uint256 _downProbability,
        int256 _signalScore,
        uint256 _stopLoss,
        uint256 _targetPrice
    ) public {

        predictions.push(
            Prediction(
                _stockName,
                _currentPrice,
                _predictedPrice,
                _direction,
                _confidence,
                _upProbability,
                _downProbability,
                _signalScore,
                _stopLoss,
                _targetPrice,
                block.timestamp
            )
        );

        emit PredictionAdded(
            predictions.length - 1,
            _stockName,
            _direction,
            _currentPrice,
            _predictedPrice,
            _confidence,
            block.timestamp
        );
    }

    function getPrediction(
        uint256 index
    )
        public
        view
        returns (
            string memory,
            uint256,
            uint256,
            string memory,
            uint256,
            uint256,
            uint256,
            int256,
            uint256,
            uint256,
            uint256
        )
    {

        Prediction memory p = predictions[index];

        return (
            p.stockName,
            p.currentPrice,
            p.predictedPrice,
            p.direction,
            p.confidence,
            p.upProbability,
            p.downProbability,
            p.signalScore,
            p.stopLoss,
            p.targetPrice,
            p.timestamp
        );
    }

    function getPredictionCount()
        public
        view
        returns (uint256)
    {
        return predictions.length;
    }
}