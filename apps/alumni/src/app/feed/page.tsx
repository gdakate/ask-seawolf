"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFeed, createPost, deletePost, getComments, addComment, toggleLike, type Post } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";

const TAGS = ["#career","#internship","#research","#networking","#advice","#general","#events","#jobs"];

function timeAgo(iso: string) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function PostCard({ post, myUserId }: { post: Post; myUserId: string | null }) {
  const qc = useQueryClient();
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [liked, setLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(post.likes_count);

  const { data: comments } = useQuery({
    queryKey: ["comments", post.id],
    queryFn: () => getComments(post.id),
    enabled: showComments,
  });

  const commentMut = useMutation({
    mutationFn: () => addComment(post.id, commentText),
    onSuccess: () => {
      setCommentText("");
      qc.invalidateQueries({ queryKey: ["comments", post.id] });
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => deletePost(post.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["feed"] }),
  });

  const handleLike = async () => {
    try {
      const res = await toggleLike(post.id);
      setLiked(res.liked);
      setLikesCount(res.likes_count);
    } catch {}
  };

  return (
    <div className={`glass-card rounded-xl p-5 ${post.is_pinned ? "border-[var(--accent)]/30" : ""}`}>
      {post.is_pinned && (
        <div className="text-[10px] text-[var(--accent)] font-semibold uppercase tracking-wide mb-2">📌 Pinned</div>
      )}

      {/* Author */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-[var(--accent)]/15 flex items-center justify-center text-[var(--accent)] font-bold text-sm flex-shrink-0">
            {post.author.name.charAt(0)}
          </div>
          <div>
            <Link href={`/profile/${post.author.id}`}
              className="text-sm font-semibold text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors">
              {post.author.name}
            </Link>
            <p className="text-xs text-[var(--text-muted)]">
              {post.author.job_title && post.author.current_company
                ? `${post.author.job_title} @ ${post.author.current_company}`
                : `${post.author.major} '${String(post.author.graduation_year).slice(-2)}`}
            </p>
          </div>
        </div>
        <span className="text-xs text-[var(--text-muted)] flex-shrink-0">{timeAgo(post.created_at)}</span>
      </div>

      {/* Content */}
      <p className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap mb-3">{post.content}</p>

      {/* Tags */}
      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {post.tags.map((t) => (
            <span key={t} className="text-[11px] px-2 py-0.5 rounded-full bg-[var(--accent)]/8 text-[var(--accent)] border border-[var(--accent)]/20">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-4 pt-2 border-t border-[var(--border)]">
        <button onClick={handleLike}
          className={`flex items-center gap-1.5 text-xs transition-colors ${liked ? "text-red-500" : "text-[var(--text-muted)] hover:text-red-400"}`}>
          {liked ? "❤️" : "🤍"} {likesCount}
        </button>
        <button onClick={() => setShowComments(!showComments)}
          className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">
          💬 {post.comments_count}
        </button>
        {post.author.id === myUserId && (
          <button onClick={() => deleteMut.mutate()}
            className="ml-auto text-xs text-[var(--text-muted)] hover:text-red-500 transition-colors">
            Delete
          </button>
        )}
      </div>

      {/* Comments */}
      {showComments && (
        <div className="mt-4 space-y-3">
          {(comments || []).map((c) => (
            <div key={c.id} className="flex gap-2.5">
              <div className="w-7 h-7 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center text-xs font-bold text-[var(--text-muted)] flex-shrink-0">
                {c.author.name.charAt(0)}
              </div>
              <div className="flex-1 p-2.5 rounded-lg bg-[var(--bg-secondary)] text-sm">
                <span className="font-medium text-[var(--text-secondary)] text-xs">{c.author.name} </span>
                <span className="text-[var(--text-primary)]">{c.content}</span>
              </div>
            </div>
          ))}
          <div className="flex gap-2">
            <input value={commentText} onChange={(e) => setCommentText(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && commentText.trim()) commentMut.mutate(); }}
              placeholder="Write a comment..."
              className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            <button onClick={() => commentMut.mutate()} disabled={!commentText.trim()}
              className="px-3 py-2 btn-water text-white rounded-lg text-xs disabled:opacity-40">
              Post
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function FeedPage() {
  const { isLoggedIn, loading, userId } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [content, setContent] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showCompose, setShowCompose] = useState(false);

  const { data: posts, isLoading } = useQuery({ queryKey: ["feed"], queryFn: getFeed, enabled: isLoggedIn });

  const postMut = useMutation({
    mutationFn: () => createPost(content, selectedTags),
    onSuccess: () => { setContent(""); setSelectedTags([]); setShowCompose(false); qc.invalidateQueries({ queryKey: ["feed"] }); },
  });

  useEffect(() => { if (!loading && !isLoggedIn) router.replace("/login"); }, [isLoggedIn, loading, router]);
  if (loading || !isLoggedIn) return null;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">Community</h1>
          <p className="text-sm text-[var(--text-muted)]">Connect with fellow Seawolves</p>
        </div>
        <button onClick={() => setShowCompose(!showCompose)}
          className="px-4 py-2 btn-water text-white rounded-xl text-sm font-medium">
          {showCompose ? "Cancel" : "+ Post"}
        </button>
      </div>

      {/* Compose */}
      {showCompose && (
        <div className="glass-card rounded-xl p-5 mb-6 space-y-3">
          <textarea value={content} onChange={(e) => setContent(e.target.value)}
            placeholder="Share something with the Seawolf community..."
            rows={4}
            className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60 resize-none" />
          <div className="flex flex-wrap gap-1.5">
            {TAGS.map((t) => (
              <button key={t} onClick={() => setSelectedTags(
                selectedTags.includes(t) ? selectedTags.filter((x) => x !== t) : [...selectedTags, t]
              )}
                className={`px-2.5 py-1 rounded-full text-xs transition-colors ${
                  selectedTags.includes(t)
                    ? "bg-[var(--accent)] text-white"
                    : "bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--accent)]"
                }`}>{t}</button>
            ))}
          </div>
          <button onClick={() => postMut.mutate()} disabled={!content.trim() || postMut.isPending}
            className="px-5 py-2 btn-water text-white rounded-lg text-sm font-semibold disabled:opacity-50">
            {postMut.isPending ? "Posting..." : "Post"}
          </button>
        </div>
      )}

      {/* Posts */}
      {isLoading && (
        <div className="space-y-4">
          {[1,2,3].map((i) => <div key={i} className="glass-card rounded-xl h-40 animate-pulse bg-[var(--bg-secondary)]" />)}
        </div>
      )}

      <div className="space-y-4">
        {(posts || []).map((post) => (
          <PostCard key={post.id} post={post} myUserId={userId} />
        ))}
        {posts?.length === 0 && (
          <div className="text-center py-16 text-[var(--text-muted)]">
            <div className="text-4xl mb-3">🌊</div>
            <p className="text-sm">No posts yet — be the first to share!</p>
          </div>
        )}
      </div>
    </div>
  );
}
