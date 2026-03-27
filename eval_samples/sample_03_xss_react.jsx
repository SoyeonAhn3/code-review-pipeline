import React from 'react';

function UserProfile({ user }) {
  return (
    <div>
      <h1>{user.name}</h1>
      <div dangerouslySetInnerHTML={{ __html: user.bio }} />
    </div>
  );
}

function CommentSection({ comments }) {
  const renderComment = (comment) => {
    const el = document.getElementById('comment-box');
    el.innerHTML = comment.text;
  };

  return (
    <div>
      {comments.map((c, i) => (
        <div key={i} onClick={() => renderComment(c)}>
          {c.title}
        </div>
      ))}
    </div>
  );
}

function SearchResults({ query }) {
  return (
    <div>
      <p>검색어: <span dangerouslySetInnerHTML={{ __html: query }} /></p>
    </div>
  );
}

export { UserProfile, CommentSection, SearchResults };
