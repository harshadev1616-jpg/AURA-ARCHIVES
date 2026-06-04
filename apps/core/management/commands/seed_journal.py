from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify


JOURNAL_POSTS = [
    {
        "title": "How to Make Your Candle Last Longer",
        "category": "Candle Care",
        "excerpt": "The first burn matters more than you think. A few small rituals will double the life — and the glow — of every candle you own.",
        "content": """There's a small heartbreak in watching a beautiful candle tunnel down the middle, leaving a ring of unburned wax clinging to the glass. The good news: it's almost always preventable, and the fixes take seconds.

The first burn sets the memory.
Soy wax has a memory. The very first time you light a candle, let it burn long enough for the melted pool to reach all the way to the edge of the vessel — usually two to three hours. Blow it out too early and the wax "remembers" that smaller pool, tunnelling inward every burn after. Give the first light the time it deserves and the rest take care of themselves.

Trim the wick, every single time.
Before each burn, trim the cotton wick down to about a quarter of an inch. A long wick burns hot and fast, throws soot, and flickers in a way that eats through your candle. A trimmed wick burns clean, steady, and slow. We keep a tiny pair of scissors beside ours; you'll be surprised how much it matters.

Keep it out of the draft.
An open window or a busy fan makes the flame dance — which looks lovely, but burns the wax unevenly and shortens the life of the candle. Set yours somewhere still.

Know when to stop.
Never burn a candle for more than four hours at a stretch, and always leave at least a centimetre of wax at the bottom. Past that point, the glass gets too hot and the scent fades anyway.

Treat your candle like the small, slow luxury it is, and a single Aura Archives soy candle will keep its glow — and its fragrance — for the full fifty hours we poured into it.""",
        "is_featured": True,
    },
    {
        "title": "Why We Pour in Small Batches",
        "category": "Behind the Studio",
        "excerpt": "We could make more, faster. We choose not to. Here's the quiet philosophy behind every batch we pour.",
        "content": """People ask us why we don't simply scale up — pour a thousand candles at once, fill a warehouse, move on. The honest answer is that something gets lost when you do.

A small batch is usually twenty to forty candles. It's small enough that one person can watch over the whole pour: checking the wax temperature by feel, adjusting the fragrance load when the season's humidity shifts, catching the candle that didn't set quite right before it ever reaches you.

It means we can change our minds. When a fragrance isn't singing, we can pull it and reblend the next batch without unwinding a mountain of inventory. Our Vanilla Amber Luxe has been quietly refined more than a dozen times this way — each batch a little truer than the last.

It also means every candle is a little bit human. Hand-poured wax is never perfectly identical; a Petal Crown candle's flower arrangement is never repeated twice. We've come to love those small variations. They're proof that a person made this, not a machine.

Small batches are slower and they cost us more. But they let us keep our promise: that every candle leaving the studio is one we'd happily light in our own home. That's a promise that only survives at this scale — so this is the scale we've chosen to stay.""",
        "is_featured": True,
    },
    {
        "title": "Finding Your Signature Scent",
        "category": "Fragrance Guide",
        "excerpt": "Floral, warm, or quiet and grounding? A short guide to discovering the candle that feels most like you.",
        "content": """Choosing a candle isn't really about choosing a fragrance — it's about choosing a mood you want to live inside. Here's how we'd guide a friend through it.

If you love an open window in spring.
You're drawn to brightness and air. Start with our Floral collection — Sunlit Bloom for warmth, Petal Crown for something softer and more romantic. These are the scents that make a room feel awake.

If your idea of luxury is doing nothing.
You want comfort you can sink into. Reach for the Classic collection: Vanilla Amber Luxe wraps a room like cashmere, all warm vanilla and sandalwood. It's the candle for rain on the window and a book you're in no hurry to finish.

If you're trying to slow your mind down.
You need grounding, not excitement. Our Wellness candles — led by Lavender Dreams — are blended to lower your shoulders. Light one twenty minutes before bed and let the room do the rest.

If you come alive after dark.
You want a little drama. Midnight Bloom is night jasmine and black rose over dark amber — mysterious, elegant, and unforgettable. It's the scent for the version of you that the daytime never quite sees.

Still unsure? Trust the moment, not the notes. Read the line under each candle's name — the moment it was made to preserve. The right scent is usually the one whose moment you wish you were living right now.""",
        "is_featured": False,
    },
    {
        "title": "The Quiet Ritual of Lighting a Candle",
        "category": "Slow Living",
        "excerpt": "In a world built for speed, striking a single match might be the smallest, most radical pause you take all day.",
        "content": """We named our studio Aura Archives because we believe a scent can archive a moment — store it, the way a photograph stores light, and hand it back to you whenever you light the wick.

But there's something quieter happening too, in the act of lighting itself.

Think about it: to light a candle, you have to stop. You find the matches. You trim the wick. You strike, you wait for the flame to catch, you watch it settle. For thirty seconds, you're doing exactly one thing — and in a day built for doing five things at once, thirty seconds of single-mindedness is almost a luxury.

We've started treating it as a small ceremony. Morning coffee gets a candle. The end of the workday gets a different one — a deliberate full-stop between the part of the day that belonged to other people and the part that belongs to us. Sunday evenings, when the week ahead starts pressing in, get Lavender Dreams and a hard rule: nothing urgent gets decided while it's burning.

None of this is precious. It's just a way of marking time with intention instead of letting it blur. A flame is a small thing. But lighting one on purpose — choosing the scent, choosing the moment — turns an ordinary evening into one you'll actually remember.

That's the whole idea, really. Light that preserves moments. Strike a match tonight and see what it keeps for you.""",
        "is_featured": False,
    },
]


class Command(BaseCommand):
    help = "Seed The Aura Journal with blog posts written in the brand voice."

    def handle(self, *args, **options):
        from apps.blog.models import BlogCategory, BlogPost

        created_count = 0
        for post in JOURNAL_POSTS:
            category, _ = BlogCategory.objects.get_or_create(name=post["category"])
            obj, created = BlogPost.objects.get_or_create(
                title=post["title"],
                defaults={
                    "category": category,
                    "excerpt": post["excerpt"],
                    "content": post["content"],
                    "status": "published",
                    "is_featured": post.get("is_featured", False),
                    "published_at": timezone.now(),
                    "meta_description": post["excerpt"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  + Journal: {obj.title}")
            else:
                # Refresh content/voice on existing posts
                obj.category = category
                obj.excerpt = post["excerpt"]
                obj.content = post["content"]
                obj.status = "published"
                obj.is_featured = post.get("is_featured", False)
                if not obj.published_at:
                    obj.published_at = timezone.now()
                obj.save()
                self.stdout.write(f"  ~ Updated: {obj.title}")

        self.stdout.write(self.style.SUCCESS(
            f"The Aura Journal seeded — {BlogPost.objects.filter(status='published').count()} posts published."
        ))
