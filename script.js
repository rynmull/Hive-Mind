document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const statusToken = document.getElementById("current-token");
    const profitLoss = document.getElementById("profit-loss");
    const totalProfit = document.getElementById("total-profit");
    const walletBalance = document.getElementById("wallet-balance");
    const startButton = document.getElementById("start-trading");
    const stopButton = document.getElementById("stop-trading");
    const tradeAmountInput = document.getElementById("trade-amount");
    const thresholdInput = document.getElementById("threshold-input");
    const profitTakeInput = document.getElementById("profit-take-input");
    const lossCutInput = document.getElementById("loss-cut-input");
    const saveSettingsButton = document.getElementById("save-settings");
    const tradesList = document.getElementById("trades-list");
    const themeToggleButton = document.getElementById("toggle-theme");

    let trading = false;

    // Dark Mode Toggle
    themeToggleButton.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        themeToggleButton.textContent = document.body.classList.contains("dark") ? "Light Mode" : "Dark Mode";
    });

    // Update Status
    const updateStatus = (token, profit, total) => {
        statusToken.textContent = `Current Token: ${token || "None"}`;
        profitLoss.textContent = `Profit/Loss: ${profit.toFixed(2)} SOL`;
        totalProfit.textContent = `Total Profit: ${total.toFixed(2)} SOL`;
    };

    // Update Wallet Balance
    const updateWalletBalance = async () => {
        try {
            const response = await fetch("/api/get-balance");
            const data = await response.json();
            walletBalance.textContent = `${data.balance} SOL`;
        } catch (error) {
            console.error("Error fetching wallet balance:", error);
        }
    };

    // Display Recent Trades
    const displayRecentTrades = (trades) => {
        tradesList.innerHTML = ""; // Clear old trades
        trades.forEach(trade => {
            const li = document.createElement("li");
            li.textContent = `${trade.action.toUpperCase()} - Token: ${trade.token}, Price: ${trade.price.toFixed(2)} SOL at ${trade.time}`;
            tradesList.appendChild(li);
        });
    };

    // Start Trading
    const startTrading = async () => {
        console.log("Start Trading button clicked."); // Debug log for button click

        trading = true;
        startButton.disabled = true;
        stopButton.disabled = false;

        const tradeAmount = parseFloat(tradeAmountInput.value);
        console.log("Trading flag set to:", trading);
        console.log("Trade amount entered:", tradeAmount);

        while (trading) {
            try {
                const response = await fetch("/api/start-trading", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ amount: tradeAmount })
                });

                console.log("Request sent to backend."); // Debug log for request sent

                const data = await response.json();
                console.log("Response from backend:", data); // Debug log for backend response

                if (data.success) {
                    updateStatus(data.token, data.profit, data.totalProfit);
                    displayRecentTrades(data.recentTrades); // Update trades list
                } else {
                    console.error("Error in backend response:", data.message);
                }
            } catch (error) {
                console.error("Error communicating with backend:", error);
            }

            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    };


    // Stop Trading
    const stopTrading = async () => {
        trading = false;
        startButton.disabled = false;
        stopButton.disabled = true;

        try {
            const response = await fetch("/api/stop-trading", { method: "POST" });
            const data = await response.json();
            console.log("Trading stopped. Recent trades:", data.recentTrades);
        } catch (error) {
            console.error("Error stopping trading:", error);
        }
    };

    // Save Settings
    const updateParameters = async () => {
        const trendingThreshold = parseInt(thresholdInput.value);
        const profitTake = parseFloat(profitTakeInput.value);
        const lossCut = parseFloat(lossCutInput.value);

        try {
            const response = await fetch("/api/update-parameters", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    trending_threshold: trendingThreshold,
                    profit_take_percentage: profitTake,
                    loss_cut_percentage: lossCut
                })
            });

            const data = await response.json();
            if (data.success) {
                alert("Parameters updated successfully!");
            }
        } catch (error) {
            console.error("Error updating parameters:", error);
        }
    };

    // Button Event Listeners
    startButton.addEventListener("click", startTrading);
    stopButton.addEventListener("click", stopTrading);
    saveSettingsButton.addEventListener("click", updateParameters);

    // Initialize
    updateStatus(null, 0, 0);
    updateWalletBalance();
    setInterval(updateWalletBalance, 10000); // Update balance every 10 seconds
});
