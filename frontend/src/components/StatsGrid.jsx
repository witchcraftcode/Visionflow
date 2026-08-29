export default function StatsGrid({ stats }) {
  return (
    <section className="stats-grid section-band" aria-label="Live platform metrics">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <article className={`stat-card tone-${stat.tone}`} key={stat.label}>
            <div className="stat-topline">
              <span>{stat.label}</span>
              <div className="stat-icon">
                <Icon size={18} />
              </div>
            </div>
            <strong>{stat.value}</strong>
            <p>{stat.detail}</p>
          </article>
        );
      })}
    </section>
  );
}
