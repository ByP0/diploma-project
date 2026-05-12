import { Link } from "react-router-dom";
import { AppRoutes } from "@shared/config/routes";
import { PageHeader } from "@shared/ui";

export function NotFoundPage() {
  return (
    <div className="page-stack">
      <PageHeader description="The requested route is not registered in the frontend router." eyebrow="404" title="Page not found" />
      <div>
        <Link className="ds-button ds-button--secondary ds-button--md" to={AppRoutes.home}>
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
