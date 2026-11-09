import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Assessment, Concept, Course, Problem

STARTER = """import java.util.*;
public class Main {
  public static void main(String[] args) {
    Scanner in = new Scanner(System.in);
    int n = in.nextInt();
    int[] values = new int[n];
    for (int i = 0; i < n; i++) values[i] = in.nextInt();
    // Print the maximum value.
  }
}"""

def seed(db: Session):
    if db.scalar(select(Course.id).limit(1)): return
    data = json.loads((Path(__file__).parent / "data" / "curriculum.json").read_text())
    course = Course(slug=data["slug"], title=data["title"], description=data["description"]); db.add(course); db.flush()
    ids = []
    for position, item in enumerate(data["concepts"], 1):
        concept = Concept(course_id=course.id, position=position, **item); db.add(concept); db.flush()
        problem = Problem(concept_id=concept.id, title=f"{concept.title}: Core Practice", statement=f"Read n integers and print their maximum value. Use the {concept.title.lower()} ideas from this lesson where relevant.", difficulty="easy" if position < 5 else "medium", starter_code=STARTER, visible_cases=[{"input":"5\n3 8 2 7 1\n","expected":"8\n","visible":True}], hidden_cases=[{"input":"1\n-4\n","expected":"-4\n","visible":False},{"input":"4\n-9 -2 -7 -3\n","expected":"-2\n","visible":False}]); db.add(problem); db.flush(); ids.append(problem.id)
    db.add(Assessment(title="Independent DSA Foundations Check", kind="mixed", difficulty="mixed", duration_minutes=35, problem_ids=ids[::2])); db.commit()
