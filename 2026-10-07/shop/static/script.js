const searchInput = document.getElementById("search-input");
const productRows = document.querySelectorAll(".product-row");
const emptyMessage = document.getElementById("empty-message");

if (!searchInput || !emptyMessage) {
    // Server-side search remains available when JavaScript is disabled.
} else {
searchInput.addEventListener("input", () => {
    const keyword = searchInput.value.trim().toLowerCase();
    let visibleCount = 0;

    productRows.forEach((row) => {
        const productName = row.cells[0].textContent.toLowerCase();
        const isVisible = productName.includes(keyword);

        row.hidden = !isVisible;
        if (isVisible) visibleCount += 1;
    });

    emptyMessage.hidden = visibleCount !== 0;
});
}
