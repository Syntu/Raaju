<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEPSE Data</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="col-md-4">
        <div class="card mt-2">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0" id="nepse-table">
                    <tbody>
                        <tr>
                            <td colspan="2" class="bg-primary text-white text-bold">
                                <select class="form-control">
                                    <option value="NEPSE">NEPSE</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Date</td>
                            <td id="date">2025-01-01</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Current</td>
                            <td id="current">2455.33</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold line-1-3">Daily Gain</td>
                            <td id="daily-gain">+15.23</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Turnover</td>
                            <td id="turnover">Rs. 1,234,567</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Previous Close</td>
                            <td id="previous-close">2440.10</td>
                        </tr>
                        <tr class="bg-secondary text-white large text-bold">
                            <td colspan="2">Market Sentiment</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Positive Stocks</td>
                            <td id="positive-stocks">60</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Neutral Stocks</td>
                            <td id="neutral-stocks">10</td>
                        </tr>
                        <tr>
                            <td class="text-left text-bold">Negative Stocks</td>
                            <td id="negative-stocks">30</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="mt-3">
            <h5 class="box_header">Market Summary</h5>
            <div class="card">
                <div class="card-body p-0 table-responsive">
                    <table class="table table-hover table-striped table-bordered mb-0">
                        <tbody>
                            <tr>
                                <th class="font-weight-bold">Total Turnover Rs:</th>
                                <td id="total-turnover">Rs. 25,000,000</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Traded Shares</th>
                                <td id="total-traded-shares">125,000</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Transactions</th>
                                <td id="total-transactions">1,500</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Scrips Traded</th>
                                <td id="total-scrips-traded">50</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">Total Float Market Capitalization Rs:</th>
                                <td id="total-float-market-cap">Rs. 900,000,000</td>
                            </tr>
                            <tr>
                                <th class="font-weight-bold">NEPSE Market Cap</th>
                                <td id="nepse-market-cap">Rs. 1,200,000,000</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
