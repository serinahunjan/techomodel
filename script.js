function startAssessment() {
  const mainContent = document.querySelector(".main-content");
  const questionArea = document.getElementById("question-area");

  mainContent.style.display = "none";

  questionArea.innerHTML = `
    <h2>Question 1</h2>
    <p>I feel that technology increases my workload.</p>
    <button onclick="submitDemo()">Submit Demo Answers</button>
  `;
}

async function submitDemo() {
  const answers = Array(30).fill(1);

  try {
    const response = await fetch("/score", {   // ✅ FIXED HERE
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ answers: answers })
    });

    if (!response.ok) {
      throw new Error("Failed to submit assessment");
    }

    const data = await response.json();
    console.log(data);

    document.getElementById("question-area").innerHTML = `
      <h2>Your Result</h2>
      <p><strong>Score:</strong> ${data.score}</p>
      <p><strong>Category:</strong> ${data.category}</p>
      <p><strong>Overload:</strong> ${data.dimensions.overload}</p>
      <p><strong>Invasion:</strong> ${data.dimensions.invasion}</p>
      <p><strong>Complexity:</strong> ${data.dimensions.complexity}</p>
    `;

  } catch (error) {
    console.error(error);

    document.getElementById("question-area").innerHTML = `
      <p style="color:red;">Error submitting assessment. Please try again.</p>
    `;
  }
}
