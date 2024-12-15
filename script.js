document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const statusToken = document.getElementById("current-token");
    const tokenBuys = document.getElementById("token-buys");
    const tokenPrice = document.getElementById("token-price");
    const walletBalance = document.getElementById("wallet-balance");
    const startButton = document.getElementById("start-trading");
    const stopButton = document.getElementById("stop-trading");
    const tradeAmountInput = document.getElementById("trade-amount");
    const thresholdInput = document.getElementById("threshold-input");
    const profitTakeInput = document.getElementById("profit-take-input");
    const lossCutInput = document.getElementById("loss-cut-input");
    const saveSettingsButton = document.getElementById("save-settings");
    const themeToggleButton = document.getElementById("toggle-theme");

    let trading = false;

    // Dark Mode Toggle
    themeToggleButton.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        themeToggleButton.textContent = document.body.classList.contains("dark") ? "Light Mode" : "Dark Mode";
    });

    // Update Status
    const updateStatus = (token, buys, price) => {
        statusToken.textContent = `Current Token: ${token || "None"}`;
        tokenBuys.textContent = `Buys: ${buys || 0}`;
        tokenPrice.textContent = `Price: ${price ? price.toFixed(2) : "0.00"} SOL`;
    };


    // Update Wallet Balance
    const updateWalletBalance = async () => {
        try {
            const response = await fetch("/api/get-balance");
            const data = await response.json();
            walletBalance.textContent = `${data.balance.toFixed(2)} SOL`;
        } catch (error) {
            console.error("Error fetching wallet balance:", error);
            walletBalance.textContent = "Error fetching balance";
        }
    };

    // Start Trading
    const startTrading = async () => {
        trading = true;
        startButton.disabled = true;
        stopButton.disabled = false;

        const tradeAmount = parseFloat(tradeAmountInput.value);
        console.log("Trading started with amount:", tradeAmount);

        while (trading) {
            try {
                const response = await fetch("/api/status");
                const data = await response.json();
                updateStatus(data.current_token, data.current_token_buys, data.buy_price);
            } catch (error) {
                console.error("Error fetching trading status:", error);
            }

            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    };

    // Stop Trading
    const stopTrading = () => {
        trading = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        console.log("Trading stopped.");
    };

    // Save Settings
    const saveSettings = async () => {
        const trendingThreshold = parseInt(thresholdInput.value, 10);
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
                alert("Settings saved successfully!");
            }
        } catch (error) {
            console.error("Error saving settings:", error);
        }
    };

    // Attach Event Listeners
    startButton.addEventListener("click", startTrading);
    stopButton.addEventListener("click", stopTrading);
    saveSettingsButton.addEventListener("click", saveSettings);

    // Initialize
    updateStatus(null, 0, 0);
    updateWalletBalance();
    setInterval(updateWalletBalance, 10000); // Refresh wallet balance every 10 seconds
});
