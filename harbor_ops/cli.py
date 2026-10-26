"""harbor-ops command line.

Commands:

    board            the sailing board (timetable season comes from
                     the derived state; default season is summer)
    freeze           release-freeze status from the derived state
    oncall           the on-call rota from the derived state
    canary           show / toggle the new-checkout canary locally
    status           every derived key, with record counts

Everything except ``canary`` is a read-only view of the derived
state. ``canary`` writes only to the local demo file (see state.py).
"""

import argparse
import sys

from . import state as state_mod


def cmd_board(args, derived):
    season = derived["state"].get("schedule.season", "summer")
    timetable = state_mod.load_timetable()
    sailings = timetable["seasons"][season]
    print(f"Sailing board - {season} timetable")
    print(f"{'DEPARTS':<8} {'ROUTE':<28} VESSEL")
    for s in sailings:
        route = f"{s['from']} -> {s['to']}"
        print(f"{s['time']:<8} {route:<28} {s['vessel']}")
    print(f"{len(sailings)} sailings. Season from derived state "
          f"(schedule.season = {season}).")
    return 0


def cmd_freeze(args, derived):
    value = derived["state"]["release.freeze"]
    winner = state_mod.winner_for(derived, "release.freeze")
    decided = f" (decided by {winner})" if winner else ""
    if value == "none":
        print(f"release.freeze: none - no release freeze in force{decided}.")
    else:
        print(f"release.freeze: {value} - releases are frozen{decided}.")
    return 0


def cmd_oncall(args, derived):
    value = derived["state"]["oncall.primary"]
    winner = state_mod.winner_for(derived, "oncall.primary")
    decided = f" (decided by {winner})" if winner else ""
    print(f"oncall.primary: {value}{decided}")
    losers = state_mod.losers_for(derived, "oncall.primary")
    if losers:
        claims = ", ".join(
            f"{rec}" for rec in losers)
        print(f"preserved losing claims: {claims}")
    return 0


def cmd_status(args, derived):
    applied = len(derived.get("order", []))
    orphans = derived.get("orphans", [])
    total = applied + len(orphans)
    print(f"project: {derived['state'].get('project', '?')}")
    print(f"records: {total} ({applied} applied, {len(orphans)} orphaned)")
    print("derived state:")
    for key in sorted(derived["state"]):
        print(f"  {key} = {derived['state'][key]}")
    return 0


def cmd_canary(args, derived):
    path = state_mod.demo_file_path(args.demo_file)
    demo = state_mod.load_demo(path)
    if args.action == "toggle":
        current, _ = state_mod.effective_canary(derived, demo)
        new = "off" if current != "off" else "canary"
        demo[state_mod.CANARY_KEY] = new
        state_mod.save_demo(path, demo)
        print(f"feature.new_checkout: {current} -> {new} "
              f"(demo file {path}; derived state unchanged)")
        return 0
    if args.action == "reset":
        demo.pop(state_mod.CANARY_KEY, None)
        state_mod.save_demo(path, demo)
        value, _ = state_mod.effective_canary(derived, demo)
        print(f"feature.new_checkout: demo override cleared; "
              f"effective value is {value} (derived state)")
        return 0
    # default: show
    value, source = state_mod.effective_canary(derived, demo)
    derived_value = derived["state"][state_mod.CANARY_KEY]
    winner = state_mod.winner_for(derived, state_mod.CANARY_KEY)
    decided = f" (decided by {winner})" if winner else ""
    print(f"feature.new_checkout: {value} (from {source})")
    if source != "derived state":
        print(f"derived state says: {derived_value}{decided}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="harbor-ops",
        description="Ferry operations, reported from derived state.")
    parser.add_argument(
        "--demo-file",
        help="path to the local demo state file "
             "(default: $HARBOR_OPS_DEMO_FILE or ./harbor-ops-demo.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("board", help="show the sailing board")
    sub.add_parser("freeze", help="show release-freeze status")
    sub.add_parser("oncall", help="show the on-call rota")
    sub.add_parser("status", help="show all derived state")

    canary = sub.add_parser(
        "canary", help="show or locally toggle the new-checkout canary")
    canary.add_argument(
        "action", nargs="?", default="show",
        choices=["show", "toggle", "reset"],
        help="show (default), toggle the local demo value, or reset it")
    return parser


COMMANDS = {
    "board": cmd_board,
    "freeze": cmd_freeze,
    "oncall": cmd_oncall,
    "status": cmd_status,
    "canary": cmd_canary,
}


def main(argv=None):
    args = build_parser().parse_args(argv)
    derived = state_mod.load_derived()
    return COMMANDS[args.command](args, derived)


if __name__ == "__main__":
    sys.exit(main())
