function startAssessment() {
  const mainContent = document.querySelector(".main-content");
  const questionArea = document.getElementById("question-area");

  if (mainContent) {
    mainContent.style.display = "none";
  }

  questionArea.innerHTML = `
    <h2>Question 1</h2>
    <p>I feel that technology increases my workload.</p>

    <button class="primary-btn submit-btn" onclick="submitDemo()">
      Submit Demo Answers
    </button>
  `;
}

async function submitDemo() {
  const answers = Array(30).fill(1); // demo answers

  try {
    const response = await fetch("/score", {   // ✅ FIXED (no localhost)
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ answers: answers })
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();
    console.log(data);

    // store result so results page can use it
    localStorage.setItem("technomindResult", JSON.stringify(data));

    document.getElementById("question-area").innerHTML = `
      <h2>Your Result</h2>
      <p><strong>Score:</strong> ${data.score}</p>
      <p><strong>Category:</strong> ${data.category}</p>
      <p><strong>Overload:</strong> ${data.dimensions.overload}</p>
      <p><strong>Invasion:</strong> ${data.dimensions.invasion}</p>
      <p><strong>Complexity:</strong> ${data.dimensions.complexity}</p>

      <button class="primary-btn submit-btn" onclick="goToResults()">
        View Full Results
      </button>
    `;
  } catch (error) {
    console.error(error);

    document.getElementById("question-area").innerHTML = `
      <p style="color:red;">There was a problem submitting your assessment.</p>
    `;
  }
}

function goToResults() {
  window.location.href = "/results"; // ✅ FIXED routing
}

const homepageImages = document.querySelectorAll(".section-img");

const imageObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("expanded");
      }
    });
  },
  {
    threshold: 0.4
  }
);

homepageImages.forEach((image) => {
  imageObserver.observe(image);
});
