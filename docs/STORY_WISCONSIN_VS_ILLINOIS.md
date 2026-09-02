# One Fetch, Ninety-One Investigations

I built a free tool that answers one question: for any address, who represents you? Not just
your member of Congress — your ward, your school board seat, your county board district,
your library board, your fire protection district. All of it, from one typed address, with
no account and nothing to install.

I started in Chicago. Illinois is now at 91 of its 102 counties. I've since done the same
thing for Wisconsin and Iowa, and the difference in how long each state took is, on its own,
worth telling you about — because the reason has almost nothing to do with effort, and almost
everything to do with a single Wisconsin law that most of its own residents have probably
never heard of.

## The hardest layer

Of everything a county government publishes, the one I found hardest to get right, over and
over, was its own board of supervisors' or commissioners' district map — the lines that decide
which few thousand people share a representative on the body that runs the county. It sounds
like it should be simple. It almost never was.

In Illinois, getting that single map right has meant, county by county: reading a district
map out of a PDF that turned out to contain no image at all, only vector drawing instructions,
by matching each filled shape's exact fill color to a legend and then anchoring the whole
drawing to the real world by matching its aspect ratio to a coordinate system, to four decimal
places. It has meant chasing down a "site is unreachable" error that turned out to be a
perfectly good website serving an incomplete security certificate — invisible to any human
using a browser, fatal to any script, and once I learned to recognize it, a pattern that
explained two other counties I'd already written off. It has meant negotiating, in writing,
for a license to redraw a map one county's GIS office sells rather than gives away. It has
meant, more than once, a clerk's honest reply to a direct question: "The County Board is
elected by districts. I do not have maps available." That county still shipped — from
certified election returns instead, because the precincts themselves turned out to be whole
census units the Census Bureau already draws — but only after I found a different kind of
document that could stand in for the one that doesn't exist.

Ninety-one counties, ninety-one variations on that same investigation.

## The one-fetch state

Wisconsin has the identical problem — a district map for every county board — and it took me
one afternoon to get all 72 of them, correctly, at once.

The reason is a single line of Wisconsin state law: every county is required to file its
current supervisory-district boundaries with a legislative office twice a year, in January and
July, and that office republishes all 72 counties' boundaries as one open, public file. Illinois
has no equivalent anywhere in its state government. No office collects what Illinois's 102
county boards look like. Each county simply decides for itself whether, and how, to make that
public — which is the entire reason it took two months of individual detective work instead
of one download.

I don't want to oversell what that Wisconsin law bought me. The state office is a clearinghouse,
not an authority — it republishes whatever each county clerk sends it, and at least one
county's submission turned out to be wrong, silently merging two of its districts into one. I
caught that by checking the numbers against the county's own separate map, not by trusting the
state's file blindly. A shortcut that skips verification isn't a shortcut, it's a future
correction, so I still checked. It just meant checking one county's homework instead of
reconstructing 72 counties' homework from nothing.

## What a law can't buy you

Here's the part I think is more interesting than the speed difference, and the part I'd hate
for a "Wisconsin just works better" headline to erase: Wisconsin's law gets you the *map*. It
gets you nothing about who actually holds each seat.

There is no Wisconsin office that publishes a statewide list of county supervisors. Getting
names for all 72 counties took the same flavor of scattered, individual work Illinois
required — a plain board page here, a PDF directory there, one county's data recovered only
through the Internet Archive after its own site went dark, one board whose current roster was
linked, in plain text, right from the county's own official page — I had found the site and
never opened that link. It finished, county by county, one at a time, and the last six were the slowest
precisely because there was no statewide file to fall back on. All 1,591 seats now carry a
name or the county's own note that the seat is vacant.

That took a week of work for a state whose *maps* took one afternoon. Which is the whole
lesson: the law bought the boundaries and bought nothing else.

What actually changed for me, between the two states, is not that the messy problem got
easier. It's that the messy problem stopped multiplying the size of my own project every time
one more county closed. In Wisconsin, that whole scattered roster problem lives in one file I
update as counties come in. In Illinois, the convention I set up early on — one dedicated
script and one scheduled check per county — means every new county is still, mechanically, its
own small project. That was a choice I made when Illinois had a handful of counties and it made
sense. It stopped making sense somewhere around county 50, and by then it was too large a
change to make safely mid-flight.

## The honest number

Illinois: 91 of 102 counties, with 11 left — each one blocked by
something different (no map published anywhere, a licensing fee, a remap the county itself
never finished, a county with no reachable website at all). I'm closing the last of them by
hand this week, the same way I closed the first 91: by reading a county's own site, and
sometimes by asking.

Wisconsin: all 72 counties mapped, in three days, because one law did in an afternoon what 91
separate investigations did for its neighbor over two months. Iowa followed the same pattern
across all 99 of its counties, arriving with even less to lean on than Wisconsin had.

Iowa is also the useful counter-example, and it taught me to state the Wisconsin lesson more
carefully. Iowa's legislature does publish a statewide county-supervisor district file — so
"a statewide file exists" is not what makes the difference. Jones County simply isn't in it.
Not misspelled, not mismatched: zero rows, so that one county gets no supervisor district
from me at all. Wisconsin's file doesn't have holes like that, and the reason isn't diligence
— it's that Wisconsin's counties are *required* to file, twice a year, so a county missing
from the state's copy would be a county out of compliance. A file somebody maintains can
quietly be short a county. A file everybody must file into shows you when it isn't.

One caution I want to put in writing, because it would be easy for me to tell a tidier story
than I can support. It is tempting to read all this as "Wisconsin's counties are simply better
run than Illinois's." I checked that, and I can't stand behind it. My Wisconsin list is
hand-corrected and double-checked; my Illinois list leans much more on an automated sweep that
guesses a county's web address from its clerk's e-mail address. Those two methods fail in
opposite ways, and I have the receipts on my own: six of my 72 Wisconsin addresses turned out
to be wrong after passing an earlier check, and in Illinois I spent weeks recording Pulaski
County as unreachable when it has a perfectly good website — just on a different domain than
the one I guessed. Some of the gap I've described is a real difference between two states.
Some of it is a difference between two of my own measuring sticks, and I'd rather say so than
let a clean number do work it hasn't earned.

What I'll defend is narrower and, I think, more useful: one Wisconsin law turned 72 separate
research problems into a single download, and Illinois has no equivalent — for county board
maps, or for anything else.
