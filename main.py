import json
import os

def ask_float(prompt, lo=None, hi=None, default=None):
    while True:
        raw = input(prompt).strip()

        if raw == "" and default is not None:
            return default

        try:
            val = float(raw)
        except ValueError:
            print("  needs to be a number")
            continue

        if lo is not None and val < lo:
            print(f"  needs to be at least {lo}")
            continue
        if hi is not None and val > hi:
            print(f"  needs to be at most {hi}")
            continue

        return val


def ask_int(prompt, lo=1):
    while True:
        val = ask_float(prompt, lo=lo)

        if val == int(val):
            return int(val)

        print("  needs to be a whole number")


def setup_str(str, i):
    if i == 0:
        return str
    return ""


def setup_categories():
    print("\nenter your grade breakdown")
    print("leave the name blank when you're done.\n")
    categories = []

    i = 0;
    while True:
        name = input(f"category name{setup_str(" (like \"homework\")", i)}:").strip()
        if not name:
            if not categories:
                print("  you need to add at least one category")
                continue
            break

        weight = ask_float(f"  {name} weight{setup_str(" (% of final grade)", i)}: ", lo=0, hi=100)
        count = ask_int(f"  how many {name} items total? ")

        categories.append({"name": name, "weight": weight, "count": count, "grades": []})

        used = sum(c["weight"] for c in categories)
        print(f"  (total weight so far: {used:g}%)\n")
        i+=1

    total = sum(c["weight"] for c in categories)
    if abs(total - 100) > 0.01:
        print("calculations will be scaled to {total:g}%")
    return categories


def enter_grades(categories):
    print(f"\nenter grades for each category as percentages")
    print("separate with commas\n")

    for c in categories:
        while True:
            raw = input(f"{c['name']} grades ({c['count']} items): ").strip()

            if not raw:
                c["grades"] = []
                break
            try:
                grades = [float(x) for x in raw.replace(",", " ").split()]
            except ValueError:
                print("  only put in numbers")
                continue
            if len(grades) > c["count"]:
                print(f"  you put in {len(grades)} items, but there are only {c['count']}")
                continue

            c["grades"] = grades
            break


def calculate(categories, target):
    total_weight = sum(c["weight"] for c in categories)
    earned = 0.0          # weighted points already locked in
    graded_weight = 0.0   # weight of work that's been graded
    remaining_weight = 0.0

    for c in categories:
        per_item = c["weight"] / c["count"]
        earned += per_item * sum(g / 100 for g in c["grades"])
        graded_weight += per_item * len(c["grades"])
        remaining_weight += per_item * (c["count"] - len(c["grades"]))

    print("\n" + "="*50)
    print("BREAKDOWN")
    print("="*50)

    for c in categories:
        if c["grades"]:
            avg = sum(c["grades"]) / len(c["grades"])
            print(f"{c['name']:<20} {avg:6.2f}%  ({len(c['grades'])}/{c['count']} graded, {c['weight']:g}% weight)")
        else:
            print(f"{c['name']:<20}   ---    (0/{c['count']} graded, {c['weight']:g}% weight)")

    print("-" * 50)

    if graded_weight == 0:
        print("nothing graded yet")
    else:
        current = earned / graded_weight * 100
        print(f"current grade: {current:.2f}%")

    # Convert target % of the full course into weighted points
    needed_points = target / 100 * total_weight
    if remaining_weight == 0:
        final = earned / total_weight * 100
        print(f"\neverything is graded, Final grade: {final:.2f}%")
        print("you got an A" if final >= target else f"you missed the {target:g}% cutoff")
        return

    print(f"weight still ungraded: {remaining_weight / total_weight * 100:.1f}%")
    needed_avg = (needed_points - earned) / remaining_weight * 100

    print()
    if needed_avg <= 0:
        print(f"you've already locked in {target:g}%. get a zero on everything else and you'll be fine")
    elif needed_avg > 100:
        print("an A is impossible without extra credit")
        print(f"you need an average of {needed_avg:.2f}% on everything else for an A")
    else:
        print(f"you need an average of {needed_avg:.2f}% on everything else for an A")

    print("\n\"what if\" final grades:")
    for avg in (100, 90, 80, 70):
        final = (earned + remaining_weight * avg / 100) / total_weight * 100
        print(f"  avg {avg:>3}% on the rest -> {final:6.2f}%")


CLASSES_FOLDER = "classes"


def file_exists(file):
    return os.path.exists(os.path.join(CLASSES_FOLDER, file))


def save(file, categories, target):
    with open(os.path.join(CLASSES_FOLDER, file), "w") as f:
        json.dump({"categories": categories, "target": target}, f, indent=2)
    print(f"Saved to {file}")


def load(file):
    with open(os.path.join(CLASSES_FOLDER, file)) as f:
        data = json.load(f)
    return data["categories"], data["target"]


def main():
    print("=== gaa (get an A) ===")
    file = None
    categories = None
    target = 90.0

    while True:
        raw = input("json file to load (name_of_course.json, blank for new): ").strip().lower()
        file = raw + ".json"

        if not raw:
            break;
        if file_exists(file):
            categories, target = load(file)
            break;
        print(f"couldn't find \"{file}\"")

    if not file_exists(file):
        file = None

    if categories is None:
        categories = setup_categories()
        target = ask_float("\ngrade cutoff for an A (default 90): ", lo=0, hi=200, default=90.0)
        enter_grades(categories)

    while True:
        calculate(categories, target)
        print("\noptions: [g] re-enter grades  [s] save  [r] restart from scratch  [q] quit")
        choice = input("> ").strip().lower()
        if choice == "g":
            enter_grades(categories)
        elif choice == "s":
            if file is None:
                while True:
                    raw = input("\nname of class (will be name of json file): ").strip().lower()
                    file = raw + ".json"
                    if not raw:
                        print("name can't be blank")
                        continue
                    if file_exists(file):
                        print("file with that name already exists")
                        continue
                    break
            save(file, categories, target)
        elif choice == "r":
            categories = setup_categories()
            target = ask_float("\nGrade cutoff for an A (default 90): ", lo=0, hi=200, default=90.0)
            enter_grades(categories)
        elif choice == "q":
            break


if __name__ == "__main__":
    main()