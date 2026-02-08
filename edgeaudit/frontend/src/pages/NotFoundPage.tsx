import { Link } from 'react-router-dom';
import { Container } from '../components/layout/Container';

export function NotFoundPage() {
  return (
    <Container>
      <div className="text-center py-16">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <Link
          to="/"
          className="mt-8 inline-block px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Go to Dashboard
        </Link>
      </div>
    </Container>
  );
}
